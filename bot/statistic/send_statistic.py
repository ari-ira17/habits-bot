from datetime import datetime, timedelta, timezone
from aiogram import Router, types
from sqlalchemy import select, update, func
import logging
import random
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bot'))
from models import User, Habit
from db import get_db
from advices import supporting_tips, weekly_motivations, daily_motivations


router = Router(name=__name__)
logger = logging.getLogger(__name__)

async def send_daily_statistic_if_time(bot):

    from .generate_statistic import generate_statistic_image

    logger.debug("Checking for daily statistics...")

    async for session in get_db():
        users_result = await session.execute(
            select(User.id, User.timezone_offset)
            .where(User.timezone_offset.isnot(None))
        )
        users = users_result.all()

        for user in users:
            user_id = user.id
            timezone_offset = user.timezone_offset
            
            user_tz = timezone(timedelta(seconds=timezone_offset))
            now_user_tz = datetime.now(user_tz)
            
            if now_user_tz.hour != 7 or now_user_tz.minute != 0:
                continue
                
            try:
                image_bytes = await generate_statistic_image(user_id, session)
                motivation = random.choice(daily_motivations)
                
                await bot.send_photo(
                    chat_id=user_id,
                    photo=types.BufferedInputFile(
                        image_bytes.read(),
                        filename="daily_statistic.png"
                    ),
                    caption=f"📊 Ежедневный отчёт по привычкам\n\n{motivation}"
                )
                
                logger.info(f"Daily statistic sent to user {user_id}")
                
            except Exception as e:
                logger.error(f"Failed to send daily statistic to user {user_id}: {e}")


async def send_weekly_statistic_if_time(bot):

    from .generate_statistic import generate_weekly_statistic_image
    from habit.calculate_percentage import calculate_completion_percentage, calculate_weekly_completion_percentage

    logger.debug("Checking for weekly statistics...")
    
    async for session in get_db():
        users_result = await session.execute(
            select(User.id, User.timezone_offset)
            .where(User.timezone_offset.isnot(None))
        )
        users = users_result.all()

        for user in users:
            user_id = user.id
            timezone_offset = user.timezone_offset

            user_tz = timezone(timedelta(seconds=timezone_offset))
            now_user_tz = datetime.now(user_tz)

            if now_user_tz.weekday() != 6 or now_user_tz.hour != 9 or now_user_tz.minute != 0:  
                continue
                
            try:
                end_date = datetime.now(timezone.utc)
                start_date = end_date - timedelta(days=7)
                
                habits_result = await session.execute(
                    select(Habit).where(Habit.user_id == user_id, Habit.is_active.is_(True))
                )
                habits = habits_result.scalars().all()
                
                habit_changes = []
                has_negative_change = False
                for habit in habits:
                    current_percentage = await calculate_completion_percentage(habit.id)
                    past_percentage = await calculate_weekly_completion_percentage(habit.id, start_date)
                    change_percentage = current_percentage - past_percentage
                    habit_changes.append({
                        'name': habit.name,
                        'change': change_percentage,
                        'current': current_percentage
                    })
                    if change_percentage <= 0:
                        has_negative_change = True
                
                image_bytes = await generate_weekly_statistic_image(user_id, session)

                if has_negative_change:
                    motivation = random.choice(supporting_tips)
                else:
                    motivation = random.choice(weekly_motivations)
                
                await bot.send_photo(
                    chat_id=user_id,
                    photo=types.BufferedInputFile(
                        image_bytes.read(),
                        filename="weekly_statistic.png"
                    ),
                    caption=f"📊 Недельный отчёт по привычкам\n\n{motivation}"
                )
                
                logger.info(f"Weekly statistic sent to user {user_id}")
                
            except Exception as e:
                logger.error(f"Failed to send weekly statistic to user {user_id}: {e}")
