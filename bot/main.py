import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from create_bot import bot, dp
from handlers import router as common_router
from habit import router as habit_router
from statistic import router as statistic_router
from db import check_db_connection_and_schema, engine
from models import Base, User, Habit, HabitCompletion

async def show_habits():
    from db import get_db
    from sqlalchemy import select

    async for session in get_db():
        result = await session.execute(select(Habit))
        habits = result.scalars().all()

        if habits:
            print("--- Habits ---")
            for habit in habits:
                print(f"ID: {habit.id}, User ID: {habit.user_id}, Name: {habit.name}, "
                      f"Active: {habit.is_active}, Config: {habit.reminder_config}, "
                      f"Last Reminded: {habit.last_reminded_at}, Next Reminder: {habit.next_reminder_datetime_utc}")
        else:
            print("Таблица habits пуста.")
        break


async def main():
    await check_db_connection_and_schema()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await show_habits()

    dp.include_router(common_router)
    dp.include_router(habit_router)
    dp.include_router(statistic_router)

    from habit.scheduler import start_scheduler
    start_scheduler(bot)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
