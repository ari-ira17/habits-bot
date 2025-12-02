from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from aiogram import Router, types
from sqlalchemy import select, update, func
import logging
import random
import sys
import os

from keyboards.inline_keyboards.done_habit_kb import done_habit_kb
from statistic.generate_statistic import generate_statistic_image, generate_weekly_statistic_image
from habit.calculate_percentage import calculate_completion_percentage, calculate_weekly_completion_percentage

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bot'))
from create_bot import scheduler
from models import User, Habit, HabitCompletion
from db import get_db
from crud import update_habit_next_reminder
from advices import supporting_tips, weekly_motivations, daily_motivations


logger = logging.getLogger(__name__)
router = Router(name=__name__)


def calculate_next_reminder(reminder_config, user_timezone_offset, last_reminded_at=None):
    user_tz = ZoneInfo('UTC') 
    

    user_tz = timezone(timedelta(seconds=user_timezone_offset))
    now_user_tz = datetime.now(user_tz)

    habit_type = reminder_config.get("type")
    time_to_check_str = reminder_config.get("time_to_check", "00:00")
    time_to_check = datetime.strptime(time_to_check_str, "%H:%M").time()
    naive_dt = datetime.combine(now_user_tz.date(), time_to_check)
    next_reminder_local = naive_dt.replace(tzinfo=user_tz)

    if habit_type == "by_days":
        num_days = reminder_config.get("num_days", 1)
        if last_reminded_at:
            last_local = last_reminded_at.astimezone(user_tz) 
            next_reminder_local = datetime.combine(
                (last_local + timedelta(days=num_days)).date(),
                time_to_check,
                tzinfo=user_tz
            )
        else:
            if now_user_tz.time() > time_to_check:
                next_reminder_local = datetime.combine(
                    (now_user_tz.date() + timedelta(days=num_days)),
                    time_to_check,
                    tzinfo=user_tz
                )
            else:
                if num_days == 1:
                    pass
                else:
                    next_reminder_local = datetime.combine(
                        (now_user_tz.date() + timedelta(days=num_days)),
                        time_to_check,
                        tzinfo=user_tz
                    )

    elif habit_type == "by_week":
        period_weeks = int(reminder_config.get("period_weeks", 1))
        weekdays_ru = reminder_config.get("weekdays", [])
        day_map = {"пн": 0, "вт": 1, "ср": 2, "чт": 3, "пт": 4, "сб": 5, "вс": 6}
        weekdays_target = [day_map[day.strip()] for day in weekdays_ru if day.strip() in day_map]

        if not weekdays_target:
            logger.warning(f"No valid weekdays found in config: {reminder_config}")
            return now_user_tz.astimezone(timezone.utc) + timedelta(weeks=1)

        if last_reminded_at:
            last_local = last_reminded_at.astimezone(user_tz) 
            start_date = last_local.date() + timedelta(days=1)
        else:
            start_date = now_user_tz.date() 

        next_date = None
        current_date = start_date
        max_days_to_check = (period_weeks + 1) * 7

        for _ in range(max_days_to_check):
            current_weekday = current_date.weekday()
            if current_weekday in weekdays_target:
                if last_reminded_at:
                    days_since_last = (current_date - last_local.date()).days
                    if days_since_last >= period_weeks * 7:
                        next_date = current_date
                        break
                else:
                    next_date = current_date
                    break
            current_date += timedelta(days=1)

        if next_date is None:
            logger.warning(f"Could not find a suitable date for weekly habit. Config: {reminder_config}")
            return None
        next_reminder_local = datetime.combine(next_date, time_to_check, tzinfo=user_tz)

    else:
        logger.error(f"Unknown habit type: {habit_type}")
        return None

    if next_reminder_local.tzinfo is None:
        logger.error("next_reminder_local is naive, cannot convert to UTC.")
        return None

    next_reminder_utc = next_reminder_local.astimezone(timezone.utc)
    return next_reminder_utc


async def deactivate_habit_if_completed(habit_id: int, bot, user_id: int, habit_name: str):

    completion_percentage = await calculate_completion_percentage(habit_id)
    
    if completion_percentage >= 100:

        async for session in get_db():
            stmt = update(Habit).where(Habit.id == habit_id).values(is_active=False)
            await session.execute(stmt)
            await session.commit()
        
        completion_message = (
            f"🎉 Поздравляем! Вы достигли своей цели по привычке <b>{habit_name}</b>!\n\n"
            f"Привычка успешно закреплена — Вы выполнили её 20 раз подряд! 💪\n"
            f"Привычка теперь деактивирована, и напоминания больше не будут приходить."
        )
        await bot.send_message(chat_id=user_id, text=completion_message, parse_mode='HTML')
        
        logger.info(f"Habit {habit_id} deactivated as completion reached 100%")
        return True
    return False    


async def schedule_first_reminder_for_habit(habit_id: int):
    logger.info(f"Scheduling first reminder for habit ID: {habit_id}")
    async for session in get_db():
        result = await session.execute(
            select(Habit, User.timezone_offset).join(User, Habit.user_id == User.id).where(Habit.id == habit_id)
        )
        row = result.first()
        if not row:
            logger.error(f"Habit with ID {habit_id} not found for scheduling.")
            return

        habit, user_tz_offset = row
        next_reminder_utc = calculate_next_reminder(
            reminder_config=habit.reminder_config,
            user_timezone_offset=user_tz_offset,
            last_reminded_at=None,
        )

        if next_reminder_utc:
            stmt_update_next = (
                update(Habit)
                .where(Habit.id == habit_id)
                .values(next_reminder_datetime_utc=next_reminder_utc)
            )
            await session.execute(stmt_update_next)
            logger.info(f"First reminder for habit {habit_id} set to {next_reminder_utc}")
        else:
            logger.warning(f"Could not calculate first reminder for habit {habit_id}, setting to None.")
            stmt_update_next = (
                update(Habit)
                .where(Habit.id == habit_id)
                .values(next_reminder_datetime_utc=None)
            )
            await session.execute(stmt_update_next)

        await session.commit()


async def schedule_check_reminders_and_statistics(bot):

    logger.info("Running scheduled check for reminders and statistics...")
    
    now_utc = datetime.now(timezone.utc)
    
    async for session in get_db():
        result = await session.execute(
            select(Habit).join(User).where(
                Habit.is_active == True,
                Habit.next_reminder_datetime_utc.isnot(None),
                Habit.next_reminder_datetime_utc <= now_utc
            )
        )
        due_habits = result.scalars().all()

        for habit in due_habits:
            user_id = habit.user_id
            habit_name = habit.name
            habit_id = habit.id

            try:
                notification_text = f"Напоминание: пришло время выполнить привычку <b>{habit_name}</b>!☺️\nCделано?"
                await bot.send_message(
                    chat_id=user_id,
                    text=notification_text,
                    parse_mode='HTML',
                    reply_markup=done_habit_kb(habit_id) 
                )
                logger.info(f"Sent reminder to user {user_id} for habit {habit.id} ('{habit_name}')")
            except Exception as e:
                logger.error(f"Failed to send reminder to user {user_id}: {e}")
                continue 

            stmt_update_last = (
                update(Habit)
                .where(Habit.id == habit.id)
                .values(last_reminded_at=now_utc)
            )
            await session.execute(stmt_update_last)

            user_result = await session.execute(
                select(User.timezone_offset).where(User.id == habit.user_id)
            )
            user_tz_offset = user_result.scalar_one_or_none()

            if user_tz_offset is None:
                logger.warning(f"User {habit.user_id} has no timezone_offset, skipping reminder for habit {habit.id}")
                continue

            next_reminder_utc = calculate_next_reminder(
                reminder_config=habit.reminder_config,
                user_timezone_offset=user_tz_offset,
                last_reminded_at=now_utc,
            )

            await update_habit_next_reminder(
                db_session=session,
                habit_id=habit.id,
                new_next_reminder=next_reminder_utc,
                last_reminded_at=now_utc 
            )

        await session.commit()
        logger.info(f"Checked {len(due_habits)} habits due for reminder.")

    await send_daily_statistic_if_time(bot)
    await send_weekly_statistic_if_time(bot)


async def send_daily_statistic_if_time(bot):

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


def start_scheduler(bot):

    scheduler.add_job(
        func=schedule_check_reminders_and_statistics,
        trigger="interval",
        minutes=1,
        id='check_reminders_and_statistics_job',
        kwargs={'bot': bot}
    )
    
    scheduler.start()
    logger.info("Scheduler started.")


def stop_scheduler():
    scheduler.shutdown()
    logger.info("Scheduler stopped.")
    