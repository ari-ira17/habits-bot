# -------------------- STAGE 1: BUILDER --------------------
FROM python:3.11-slim AS builder 

ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Исправлено: явное указание назначения /app/
COPY requirements.txt /app/

# Установка зависимостей
RUN apt-get update && apt-get install -y build-essential libpq-dev --no-install-recommends && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove build-essential


# -------------------- STAGE 2: FINAL (PRODUCTION IMAGE) --------------------
FROM python:3.11-slim AS final

WORKDIR /app

# Копируем установленные зависимости из builder'а
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Исправлено: Копируем код приложения в рабочую директорию /app
COPY bot /app/bot
COPY db_init /app/db_init

# Команда запуска бота
CMD ["python", "bot/main.py"]
