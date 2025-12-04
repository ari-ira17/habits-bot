from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '.', 'bot'))
from models import User, Habit, HabitCompletion
from datetime import datetime, timezone


async def get_or_create_user(db: AsyncSession, telegram_id: int, timezone_offset: int = 0):

    result = await db.execute(select(User).where(User.id == telegram_id))
    user = result.scalars().first()
    if not user:
        user = User(id=telegram_id, timezone_offset=timezone_offset)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def create_habit(db: AsyncSession, user_id: int, name: str, reminder_config: dict, next_reminder_datetime_utc: datetime):

    habit = Habit(
        user_id=user_id,
        name=name,
        reminder_config=reminder_config,
        next_reminder_datetime_utc=next_reminder_datetime_utc
    )
    db.add(habit)
    await db.commit()
    await db.refresh(habit)
    return habit


async def get_user_habits(db: AsyncSession, user_id: int):

    result = await db.execute(select(Habit).where(Habit.user_id == user_id))
    return result.scalars().all()


async def get_habits_for_reminder(db: AsyncSession):

    now_utc = datetime.now(timezone.utc)
    result = await db.execute(
        select(Habit)
        .where(Habit.next_reminder_datetime_utc <= now_utc)
        .where(Habit.is_active == True)
    )
    return result.scalars().all()


async def update_habit_next_reminder(db_session: AsyncSession, habit_id: int, new_next_reminder: datetime, last_reminded_at: datetime = None):

    values_to_update = {
        'next_reminder_datetime_utc': new_next_reminder
    }
    if last_reminded_at is not None:
        values_to_update['last_reminded_at'] = last_reminded_at

    stmt = update(Habit).where(Habit.id == habit_id).values(**values_to_update)
    await db_session.execute(stmt)

async def record_habit_completion(db_session: AsyncSession, habit_id: int, completed_at: datetime = None):
    
    if completed_at is None:
        completed_at = datetime.now(timezone.utc)

    completion = HabitCompletion(
        habit_id=habit_id,
        completed_at=completed_at
    )
    db_session.add(completion) 


async def delete_habit(db_session: AsyncSession, habit_id: int, user_id: int) -> bool:
    
    await db_session.execute(
        delete(HabitCompletion).where(HabitCompletion.habit_id == habit_id)
    )

    result = await db_session.execute(
        delete(Habit).where(Habit.id == habit_id, Habit.user_id == user_id)
    )

    await db_session.commit()
    return True
