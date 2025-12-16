import requests
import pandas as pd
import codecs, json
import io
from bs4 import BeautifulSoup
import redis
import os
import logging
import time

from utils import format_room_name

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

SHARED_DIR = os.path.join(os.path.dirname(__file__), 'shared')

try:
    r = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=int(os.getenv('REDIS_PORT', 6379)))
    last_run = r.get('scraper:last_run')
    now = int(time.time())
    if last_run is not None and now - int(last_run) < 86400: # 86400 секунд = 24 часа
        logging.info("Данные свежие, спим...")
        time.sleep(21600)  # Спим 6 часов
        exit(0)
    # Обновляем время запуска
    r.set('scraper:last_run', now)
except Exception as e:
    logging.error(f"Не удалось проверить время последнего запуска в Redis")

try:
    session = requests.session()
    logging.info("Fetching main room list from https://table.nsu.ru/room")
    response = session.get('https://table.nsu.ru/room')
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    room_links = [
        f"https://table.nsu.ru{el.get('href')}"
        for el in soup.find_all(class_='tutors_item')
        if el.get('href')[6].isdigit()
    ]
    logging.info(f"Получено {len(room_links)} ссылок на расписания аудиторий")
except Exception as e:
    logging.error(f"Не удалось получить ссылки на расписания аудиторий")
    raise

timetable_by_room = {}

for url in room_links:
    try:
        #     Каждый 50-ый показываем прогресс
        if len(timetable_by_room) % 50 == 0:
            logging.info(f"Обработано {len(timetable_by_room)} из {len(room_links)} аудиторий")

        html = session.get(url).text
        timetable_by_room[url] = pd.read_html(io.StringIO(html))[1].to_numpy().tolist()
    except Exception as e:
        logging.error(f"Не удалось обработать {url}: {e}")
    finally:
        time.sleep(1)  # спим 1 секунду после каждого запроса (даже если была ошибка)


try:
    with codecs.open(os.path.join(SHARED_DIR, 'tts.json'), 'w', encoding='utf-8') as f:
        json.dump(timetable_by_room, f, separators=(',', ':'), sort_keys=True, indent=4)
    logging.info("Расписание сохранено в tts.json")
except Exception as e:
    logging.error(f"Не удалось сохранить tts.json")

# Вычисляем ответы для бота
bot_answers = {}
for pair in range(7):
    for day in range(1, 7):
        free_rooms_new, free_rooms_old = '', ''
        for url, timetable in timetable_by_room.items():
            try:
                if pd.isna(timetable[pair][day]):
                    room_name = format_room_name(url)
                    formatted_room = f'[{room_name}]({url})\n'
                    if len(room_name.replace(' ', '')) == 4:
                        free_rooms_new += formatted_room
                    else:
                        free_rooms_old += formatted_room
            except Exception as e:
                logging.warning(f"Error processing room {url}: {e}")
        bot_answers[f"{day} {pair + 1}"] = free_rooms_new
        bot_answers[f"{day} 2{pair + 1}"] = free_rooms_old

try:
    with codecs.open(os.path.join(SHARED_DIR, 'bot_answers.json'), 'w', encoding='utf-8') as f:
        json.dump(bot_answers, f, separators=(',', ':'), sort_keys=True, indent=4)
    logging.info("Ответы сохранены bot_answers.json")
except Exception as e:
    logging.error(f"Не удалось сохранить bot_answers.json")

# Публикуем обновления в Redis
try:
    r = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=int(os.getenv('REDIS_PORT', 6379)))
    r.publish('bot_answers_update', json.dumps(bot_answers))
    logging.info("Опубликовали bot_answers_update в Redis")
except Exception as e:
    logging.error(f"Не удалось опубликовать задачу в Redis")

