FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/xerz/nsu-free-room"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
