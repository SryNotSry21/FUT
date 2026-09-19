FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY futbot ./futbot

ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/app/data/futbot.db

CMD ["python", "-m", "futbot", "bot"]
