from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from aiogram import Router
from sqlalchemy import select, update, func
import logging
import random
import sys
import os

from keyboards.inline_keyboards.done_habit_kb import done_habit_kb

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bot'))
from create_bot import scheduler
from models import User, Habit, HabitCompletion
from db import get_db
from crud import update_habit_next_reminder


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


async def calculate_completion_percentage(habit_id: int) -> int:
    async for session in get_db():
        completion_count_result = await session.execute(
            select(func.count(HabitCompletion.id)).where(HabitCompletion.habit_id == habit_id)
        )
        completion_count = completion_count_result.scalar() or 0
        percentage = min(100, (completion_count / 10) * 100)
        return int(percentage)


async def send_reminder_message(bot, user_id: int, habit_name: str, habit_id: int):
    notification = (
        f"Напоминание: пришло время выполнить привычку <b>{habit_name}</b>!☺️\n"
        f"Cделано?"
    )
    await bot.send_message(
        chat_id=user_id,
        text=notification,
        parse_mode='HTML',
        reply_markup=done_habit_kb(habit_id)  
    )


async def send_completion_message(bot, user_id: int, habit_name: str, percentage: int):
    done_habit = (
        f"Отлично! 🎉\n"
        f"Вы справились — молодец! 💪\n\n"
        f"Ваш прогресс по привычке <b>{habit_name}</b> составляет <b>{percentage}</b>%"
    )
    await bot.send_message(chat_id=user_id, text=done_habit, parse_mode='HTML')


async def send_not_done_message(bot, user_id: int, habit_name: str):
    tips = [
        "Попробуйте разбить привычку на более мелкие шаги.",
        "Найдите себе напарника по привычке.",
        "Отметьте даже минимальный прогресс!",
        "Наградите себя за выполнение.",
        "Просто начните с 2 минут.",
        "Создайте уютное место для выполнения привычки."
    ]
    random_tip = random.choice(tips)

    not_done_habit = (
        f"К сожалению, привычка не была выполнена — текущая серия прервана.\n"
        f"Ваш прогресс по привычке <b>{habit_name}</b> составляет <b>0</b>%\n\n"
        f"Продолжай стараться, и обязательно достигнешь своей цели!💫\n\n"
        f"Я подготовил совет, который может помочь тебе👊\n"
        f"{random_tip}"
    )
    await bot.send_message(chat_id=user_id, text=not_done_habit, parse_mode='HTML')


async def schedule_check_reminders(bot):
    logger.info("Running scheduled check for reminders...")
    async for session in get_db():
        now_utc = datetime.now(timezone.utc)
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


def start_scheduler(bot):
    scheduler.add_job(
        func=schedule_check_reminders,
        trigger="interval",
        minutes=1,
        id='check_reminders_job',
        kwargs={'bot': bot}
    )
    scheduler.start()
    logger.info("Scheduler started.")


def stop_scheduler():
    scheduler.shutdown()
    logger.info("Scheduler stopped.")
