import os

PROD_SECRET_PATH = "/run/secrets/bot_prod_token"

class Config:
    def __init__(self):
        self.BOT_TOKEN = self._get_bot_token()
        if not self.BOT_TOKEN:
            raise RuntimeError("BOT token is not provided. Set BOT_TOKEN env var (dev) or provide Docker secret at /run/secrets/bot_prod_token (prod).")

        self.DB_HOST = os.getenv("DB_HOST", "postgres")
        self.DB_NAME = os.getenv("DB_NAME")
        self.DB_USER = os.getenv("DB_USER")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD")

    def _get_bot_token(self):
        """Get token from Docker Secret (Prod) or os.environ (Dev)."""
        # 1. Production secret (Docker Secret)
        try:
            if os.path.exists(PROD_SECRET_PATH):
                with open(PROD_SECRET_PATH, "r") as f:
                    token = f.read().strip()
                    if token:
                        return token
        except Exception as e:
            # не фатальная ошибка чтения — логируйте / поднимайте выше при необходимости
            raise IOError(f"Docker Secret Read Error: {e}")

        # 2. Development
        return os.getenv("BOT_TOKEN")

CONFIG = Config()
