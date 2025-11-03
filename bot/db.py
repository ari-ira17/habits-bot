from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Получаем переменные окружения, установленные в docker-compose.yml
DB_HOST = os.getenv("DB_HOST", "postgres")  # Должно быть 'postgres'
DB_NAME = os.getenv("DB_NAME", "habits_db")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

# Строка подключения (асинхронная)
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Создаём асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=False) # echo=True для отладки

# Создаём фабрику сессий
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """Функция-генератор для получения сессии БД (для использования в роутерах)."""
    async with AsyncSessionLocal() as session:
        yield session

async def check_db_connection_and_schema():
    """
    Функция для проверки подключения и вывода структуры БД.
    Может вызываться из main.py при старте.
    """
    logger.info(f"Подключение к БД: {DATABASE_URL}")
    try:
        # Проверяем подключение
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1")) # Простой запрос для проверки подключения

        logger.info("✅ Подключение к БД успешно установлено.")

        # Получаем список таблиц
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))
            tables = result.fetchall()

        logger.info("--- Структура БД ---")
        if tables:
            table_names = [table[0] for table in tables]
            logger.info(f"Найдены таблицы: {', '.join(table_names)}")

            # Выводим структуру каждой таблицы
            for table_name in table_names:
                logger.info(f"\nТаблица: {table_name}")
                columns_result = await conn.execute(
                    text("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns
                        WHERE table_name = :table_name
                        ORDER BY ordinal_position;
                    """),
                    {"table_name": table_name}
                )
                columns = columns_result.fetchall()
                for col in columns:
                    nullable_str = "NULL" if col[2] == "YES" else "NOT NULL"
                    default_str = f" DEFAULT {col[3]}" if col[3] else ""
                    logger.info(f"  - {col[0]} ({col[1]}) {nullable_str}{default_str}")
        else:
            logger.info("⚠️  В схеме 'public' таблицы не найдены.")

        logger.info("--- Проверка структуры БД завершена ---")

    except Exception as e:
        logger.error(f"❌ Ошибка подключения или выполнения запроса: {e}")
        raise # Пробрасываем ошибку, чтобы основной процесс (main.py) мог её обработать
