# создание Job и ее добавление

from aiogram import Router
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo
from datetime import datetime

from .states import Habit_By_Days


router = Router()

async def habit_reminder_job(bot, user_id: int, title: str):
    try:
        await bot.send_message(user_id, f"Напоминание: пора выполнить привычку '{title}'!")
    except Exception as e:
        print(f"Ошибка при отправке напоминания пользователю {user_id}: {e}")


async def habit_by_day_scheduler(scheduler, bot, user_id: int, title: str, hours: int, minutes: int, num_days: int, user_timezone_str: str):
    job_id = f"habit_{user_id}_{title}"
    Habit_By_Days.habit_id = job_id

    try:
        user_tz = ZoneInfo(user_timezone_str)

        trigger = CronTrigger(
            day=f"*/{num_days}",
            hour=hours,
            minute=minutes,
            timezone=user_tz  
        )

        job = scheduler.add_job(
            func=habit_reminder_job,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            kwargs={'bot': bot, 'user_id': user_id, 'title': title}
        )
        print(f"Задача '{job_id}' запланирована на {num_days} дней в {hours:02d}:{minutes:02d} по времени {user_timezone_str}.")
        return True
    except Exception as e:
        print(f"Ошибка при создании задачи: {e}")
        return False


def ru_days_to_cron(days_ru: str) -> str:
    ru_to_en = {
        "пн": "mon",
        "вт": "tue",
        "ср": "wed",
        "чт": "thu",
        "пт": "fri",
        "сб": "sat",
        "вс": "sun"
    }
    days_list = [day.strip().lower() for day in days_ru.split(",")]
    cron_days = [ru_to_en[day] for day in days_list if day in ru_to_en]
    return ",".join(cron_days)


async def habit_by_week_scheduler(scheduler, bot, user_id: int, title: str, hours: int, minutes: int,
                                  weekdays_cron: str, period_weeks: int, user_timezone_str: str, created_at_iso: str):
    job_id = f"habit_week_{user_id}_{title}"

    try:
        user_tz = ZoneInfo(user_timezone_str)
        created_at = datetime.fromisoformat(created_at_iso)

        trigger = CronTrigger(
            day_of_week=weekdays_cron,
            hour=hours,
            minute=minutes,
            timezone=user_tz
        )

        job = scheduler.add_job(
            func=habit_week_reminder_job,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            kwargs={
                'bot': bot,
                'user_id': user_id,
                'title': title,
                'period_weeks': period_weeks,
                'created_at_iso': created_at_iso,
                'user_timezone_str': user_timezone_str
            }
        )
        print(f"Задача '{job_id}' запланирована: каждую неделю в {weekdays_cron} {hours:02d}:{minutes:02d} по {user_timezone_str}.")
        return True
    except Exception as e:
        print(f"Ошибка при создании задачи: {e}")
        return False


async def habit_week_reminder_job(bot, user_id: int, title: str, period_weeks: int, created_at_iso: str, user_timezone_str: str):
    try:
        user_tz = ZoneInfo(user_timezone_str)
        now = datetime.now(user_tz)
        created_at = datetime.fromisoformat(created_at_iso).astimezone(user_tz)

        weeks_passed = (now.date() - created_at.date()).days // 7

        if weeks_passed % period_weeks == 0:
            await bot.send_message(user_id, f"Напоминание: пора выполнить привычку '{title}'!")
    except Exception as e:
        print(f"Ошибка в habit_week_reminder_job: {e}")


# # напоминание о привычке

# # from keyboards.reply_keyboards.done_habit_kb import done_habit_kb
# notification = f"Напоминание: пришло время выполнить привычку <b>Привычка1</b>!☺️\n"
# f"Cделано?"
# # parse_mode=ParseMode.HTML
# # reply_markup = done_habit_kb()


# # если ответ "да"
 
# done_habit = f"Отлично! 🎉\n"
# f"Вы справились — молодец! 💪\n\n"

# f"Ваш прогресс по привычке <b>Привычка1</b> составляет <b>X</b>%"


# # если ответ "нет"
# not_done_habit = f"К сожалению, привычка не была выполнена — текущая серия прервана.\n"
# f"Ваш прогресс по привычке <b>Привычка1</b> составляет <b>0</b>%\n\n"

# f"Продолжай стараться, и обязательно достигнешь своей цели!💫\n\n"

# f"Я подготовил совет, который может помочь тебе👊\n"
# # один рандомновыбранный из списка совет
