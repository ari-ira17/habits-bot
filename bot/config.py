import os

PROD_SECRET_PATH = "/run/secrets/bot_prod_token"

def _get_bot_token():
    # 1) Дескриптор секретов Docker (prod)
    try:
        if os.path.exists(PROD_SECRET_PATH):
            with open(PROD_SECRET_PATH, "r") as f:
                token = f.read().strip()
                if token:
                    return token
    except Exception as e:
        # если чтение секрета упало — бросаем, чтобы не запускаться без токена
        raise IOError(f"Error reading Docker secret {PROD_SECRET_PATH}: {e}")

    # 2) Переменная окружения (dev)
    return os.getenv("BOT_TOKEN")

# Экспортируем BOT_TOKEN в модуль — это совместимо с существующим create_bot.py
BOT_TOKEN = _get_bot_token()
if not BOT_TOKEN:
    # Явная ошибка при отсутствии токена — поможет быстро увидеть проблему в логах
    raise RuntimeError("BOT_TOKEN is not set. Provide BOT_TOKEN env var (dev) or Docker secret at /run/secrets/bot_prod_token (prod).")

class Config:
    def __init__(self):
        self.BOT_TOKEN = BOT_TOKEN
        self.DB_HOST = os.getenv("DB_HOST", "postgres")
        self.DB_NAME = os.getenv("DB_NAME")
        self.DB_USER = os.getenv("DB_USER")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD")

CONFIG = Config()

