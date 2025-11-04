# создание Job и ее добавление

from aiogram import Router, types
from aiogram.filters import Command
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo

from create_bot import scheduler
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




@router.message(Command("my_reminders"))
async def show_reminders(message: types.Message):
    user_id = message.from_user.id
    jobs = scheduler.get_jobs()
    user_jobs = [job for job in jobs if job.id.startswith(f"habit_{user_id}_")]

    if not user_jobs:
        await message.answer("У вас пока нет запланированных напоминаний.")
        return

    text = "Ваши запланированные напоминания:\n\n"
    for job in user_jobs:

        parts = job.id.split('_', 2)
        if len(parts) == 3:
            _, _, title = parts
        else:
            title = "Неизвестная привычка"
        next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else "Неизвестно"
        text += f"- Привычка: {title}\n  Следующее напоминание: {next_run}\n\n"

    await message.answer(text)