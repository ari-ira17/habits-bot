from sqlalchemy import select, func
from aiogram import Router
import sys
import os
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bot'))
from models import HabitCompletion
from db import get_db

router = Router(name=__name__)

async def calculate_completion_percentage(habit_id: int) -> int:
    async for session in get_db():
        completion_count_result = await session.execute(
            select(func.count(HabitCompletion.id)).where(HabitCompletion.habit_id == habit_id)
        )
        completion_count = completion_count_result.scalar() or 0
        percentage = min(100, (completion_count / 10) * 100)
        return int(percentage)
    

async def calculate_weekly_completion_percentage(habit_id: int, target_date: datetime) -> int:

    async for session in get_db():
        completion_count_result = await session.execute(
            select(func.count(HabitCompletion.id)).where(
                HabitCompletion.habit_id == habit_id,
                HabitCompletion.completed_at <= target_date
            )
        )
        completion_count = completion_count_result.scalar() or 0
        percentage = min(100, (completion_count / 10) * 100)
        return int(percentage)
    