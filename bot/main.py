import asyncio

from create_bot import bot, dp
from handlers import router as common_router
from habit import router as habit_router
from db import check_db_connection_and_schema, engine
from models import Base
from habit.scheduler import start_scheduler


async def main():
    await check_db_connection_and_schema()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    dp.include_router(common_router)
    dp.include_router(habit_router)

    start_scheduler(bot)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
