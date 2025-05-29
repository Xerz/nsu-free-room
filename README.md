
# NSU Free Room Bot

> Бот запущен и доступен по адресу: [@nsu_temperature_bot](https://t.me/nsu_temperature_bot)

Телеграм-бот для поиска свободных аудиторий в НГУ по расписанию.

## Описание кейса

В НГУ часто возникает задача найти свободную аудиторию для занятий или встреч. Этот бот позволяет узнать, какие аудитории свободны в конкретный день и пару. Пользователь вводит день недели и номер пары — бот возвращает список свободных аудиторий в новом корпусе. Если перед номером пары стоит `2`, бот возвращает список свободных аудиторий в старом и лабораторном корпусах.

## Как это работает

- **Сбор расписания:** Скрипт `scraper/update-tt.py` парсит расписание аудиторий с сайта [table.nsu.ru](https://table.nsu.ru/room).
- **Вычисление свободных аудиторий:** На основе расписания формируются ответы для каждой комбинации "день + пара".
- **Хранение ответов:** Ответы сохраняются в файл `shared/bot_answers.json` для быстрого доступа при запуске бота.
- **Обновление в реальном времени:** При работе бот хранит ответы в памяти, но если скрипт обновляет расписание, новые ответы публикуются через Redis Pub/Sub и бот их подхватывает без перезапуска.
- **Архитектура:** Используется Docker Compose для запуска бота, парсера и Redis. Все сервисы используют общий том `shared` для обмена файлами.

## Структура проекта

```
nsu-free-room/
├── bot/                # Исходный код Telegram-бота
│   ├── bot.py
│   ├── constants.py
│   ├── utils.py
│   └── .env
├── scraper/            # Скрипт для парсинга расписания и генерации ответов
│   ├── update-tt.py
│   ├── utils.py
│   └── ...
├── shared/             # Общие файлы между сервисами (bot_answers.json, tts.json)
├── docker-compose.yml  # Docker Compose конфигурация
└── README.md
```

## Быстрый старт

1. **Клонируйте репозиторий:**
   ```sh
   git clone https://github.com/Xerz/nsu-free-room.git
   cd nsu-free-room
   ```

2. **Создайте файл окружения для бота:**
   ```
   bot/.env
   ```
   Пример содержимого:
   ```
   TELEGRAM_BOT_TOKEN=ваш_токен_бота
   REDIS_HOST=redis
   REDIS_PORT=6379
   ```

3. **Запустите сервисы:**
   ```sh
   docker-compose up --build
   ```

4. **Проверьте работу бота:** Найдите вашего бота в Telegram и начните диалог.

---

### Альтернативный запуск через ghcr.io

Вы можете использовать готовые образы из GitHub Container Registry (ghcr.io), не собирая их локально.

1. **Создайте файл окружения для бота** в папке `bot` и папку `shared`, если её ещё нет:

   ```sh
   mkdir -p shared
   touch bot/.env
   ```

   Убедитесь, что в `bot/.env` указан правильный токен бота.

2. **Создайте файл `docker-compose-ghcr.yml`** (или используйте уже имеющийся):

   ```yaml
   services:
     redis:
       image: redis:7-alpine
       restart: unless-stopped
       expose:
         - 6379

     bot:
       image: ghcr.io/xerz/nsu-free-room-bot:latest
       env_file:
         - ./bot/.env
       depends_on:
         - redis
       restart: unless-stopped
       volumes:
         - ./shared:/app/shared

     scraper:
       image: ghcr.io/xerz/nsu-free-room-scraper:latest
       depends_on:
         - redis
       environment:
         - REDIS_HOST=redis
         - REDIS_PORT=6379
       restart: unless-stopped
       volumes:
         - ./shared:/app/shared
   ```

3. **Запустите сервисы:**
   ```sh
   docker-compose -f docker-compose-ghcr.yml up
   ```

---

## Переменные окружения

- `TELEGRAM_BOT_TOKEN` — токен Telegram-бота (обязательно)
- `REDIS_HOST` — адрес Redis (по умолчанию `redis`)
- `REDIS_PORT` — порт Redis (по умолчанию `6379`)

## Как обновляются данные

- Скрипт парсера (`scraper/update-tt.py`) запускается периодически (можно настроить через cron или вручную).
- После парсинга новые ответы сохраняются в `shared/bot_answers.json` и публикуются в канал Redis.
- Бот автоматически подхватывает новые данные через Redis Pub/Sub, не требуя перезапуска.

## Используемые технологии

- Python 3
- [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI)
- BeautifulSoup, pandas, requests
- Redis (Pub/Sub)
- Docker, Docker Compose
