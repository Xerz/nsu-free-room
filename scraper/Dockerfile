FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/xerz/nsu-free-room"

WORKDIR /app

RUN apt-get update && apt-get install -y python3-distutils && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python", "update-tt.py"]
