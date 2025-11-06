from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '.', 'bot'))
from models import User, Habit, HabitCompletion
from datetime import datetime, timezone


async def get_or_create_user(db: AsyncSession, telegram_id: int, timezone_offset: int = 0):
    """
    Получает пользователя по telegram_id или создает нового, если не существует.
    """
    result = await db.execute(select(User).where(User.id == telegram_id))
    user = result.scalars().first()
    if not user:
        user = User(id=telegram_id, timezone_offset=timezone_offset)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def create_habit(db: AsyncSession, user_id: int, name: str, reminder_config: dict, next_reminder_datetime_utc: datetime):
    """
    Создает новую привычку для пользователя.
    """
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
    """
    Получает все привычки конкретного пользователя.
    """
    result = await db.execute(select(Habit).where(Habit.user_id == user_id))
    return result.scalars().all()

async def get_habits_for_reminder(db: AsyncSession):
    """
    Получает все активные привычки, время напоминания которых наступило.
    """
    now_utc = datetime.now(timezone.utc)
    result = await db.execute(
        select(Habit)
        .where(Habit.next_reminder_datetime_utc <= now_utc)
        .where(Habit.is_active == True)
    )
    return result.scalars().all()

async def update_habit_next_reminder(db: AsyncSession, habit_id: int, new_next_reminder: datetime, last_reminded_at: datetime = None):
    """
    Обновляет время следующего напоминания и (опционально) время последнего напоминания.
    """
    values_to_update = {
        Habit.next_reminder_datetime_utc: new_next_reminder
    }
    if last_reminded_at:
        values_to_update[Habit.last_reminded_at] = last_reminded_at

    stmt = update(Habit).where(Habit.id == habit_id).values(**values_to_update)
    await db.execute(stmt)
    await db.commit()


async def record_habit_completion(db: AsyncSession, habit_id: int):
    """
    Записывает выполнение привычки.
    """
    completion = HabitCompletion(
        habit_id=habit_id,
        completed_at=datetime.now(timezone.utc) # Всегда записываем в UTC
    )
    db.add(completion)
    await db.commit()
    await db.refresh(completion)
    return completion
