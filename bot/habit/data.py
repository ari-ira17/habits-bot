from sqlalchemy import select
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bot'))
from models import User, Habit
from db import get_db
from .scheduler import schedule_first_reminder_for_habit


async def save_habit_by_day_to_db(data: dict):

    async for session in get_db():
        result = await session.execute(select(User).where(User.id == data['owner_id']))
        user = result.scalar_one_or_none()

        reminder_config = {
            "type": "by_days",
            "num_days": data['num_days'],
            "time_to_check": data['time_to_check']
        }

        habit = Habit(
            user_id=user.id,
            name=data['title'],
            is_active=True,
            reminder_config=reminder_config
        )

        session.add(habit)
        await session.commit()
        await session.refresh(habit)

        print(f"Привычка '{habit.name}' (ID: {habit.id}) сохранена в БД для пользователя {user.id}")
        
        await schedule_first_reminder_for_habit(habit.id)


async def save_habit_by_week_to_db(data: dict):
    
    async for session in get_db():
        result = await session.execute(select(User).where(User.id == data['owner_id']))
        user = result.scalar_one_or_none()

        weekdays_input = data['weekdays']
        weekdays_list = [day.strip() for day in weekdays_input.lower().split(",") if day.strip()]

        reminder_config = {
            "type": "by_week",
            "period_weeks": data['period'],  
            "weekdays": weekdays_list,      
            "time_to_check": data['time_to_check']  
        }

        habit = Habit(
            user_id=user.id,
            name=data['title'],
            is_active=True,
            reminder_config=reminder_config
        )

        session.add(habit)
        await session.commit()
        await session.refresh(habit)

        print(f"Привычка '{habit.name}' (ID: {habit.id}) сохранена в БД для пользователя {user.id} (по неделям).")
        
        await schedule_first_reminder_for_habit(habit.id)
