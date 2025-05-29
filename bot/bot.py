import telebot
import os
from dotenv import load_dotenv
from constants import ERROR_MESSAGE, WEEK_KEYBOARD
from utils import load_answers
import threading
import redis
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

load_dotenv()
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

bot = telebot.TeleBot(API_TOKEN, parse_mode='MARKDOWN')

# Загружаем ответы один раз при старте
bot_answers = {}
try:
    bot_answers = load_answers()
except Exception as e:
    logging.error(f"Не удалось загрузить ответы из файла")
    bot_answers = {}

def redis_listener():
    r = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=int(os.getenv('REDIS_PORT', 6379)), decode_responses=True)
    pubsub = r.pubsub()
    pubsub.subscribe('bot_answers_update')
    for message in pubsub.listen():
        if message['type'] == 'message':
            try:
                global bot_answers
                bot_answers = json.loads(message['data'])
                logging.info("bot_answers обновлены из Redis Pub/Sub")
            except Exception as exc:
                logging.error("Ошибка при обновлении bot_answers из Redis: %s", exc)

# Запускаем слушатель Redis в отдельном потоке
threading.Thread(target=redis_listener, daemon=True).start()

@bot.message_handler(func=lambda message: True)
def handle_user_message(message):
    """
    Обрабатывает входящее сообщение пользователя, ищет свободные аудитории и отправляет ответ.
    """
    try:
        bot.reply_to(message, bot_answers[message.text], disable_web_page_preview=True, reply_markup=WEEK_KEYBOARD)
        logging.info("Ответ отправлен пользователю %s: %s", message.from_user.id, message.text)
    except Exception as exc:
        bot.reply_to(message, ERROR_MESSAGE)
        logging.warning("Ошибка при обработке сообщения '%s' от пользователя %s", message.text, message.from_user.id)

bot.polling()
