import asyncio
from create_bot import bot, dp
from handlers import router as common_router
from habit import router as habit_router
from create_bot import scheduler
from db import check_db_connection_and_schema

async def main():
    await check_db_connection_and_schema()
    dp.include_router(common_router)
    dp.include_router(habit_router)
    await bot.delete_webhook(drop_pending_updates=True)
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
    