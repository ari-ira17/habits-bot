# создание Job и ее добавление

# testing Scheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from create_bot import bot, scheduler

router = Router()

async def my_scheduled_task(chat_id: int):
    await bot.send_message(
        chat_id=chat_id,
        text="Планировщик сработал!"
    )

@router.message(Command("set_time"))
async def set_time_comand(message: Message):
    scheduler.add_job(
        my_scheduled_task, 
        'interval', 
        seconds=5,
        args=[message.chat.id]
    )
    await message.answer("Планировщик запущен!")



# напоминание о привычке

# from keyboards.reply_keyboards.done_habit_kb import done_habit_kb
notification = f"Напоминание: пришло время выполнить привычку <b>Привычка1</b>!☺️\n"
f"Cделано?"
# parse_mode=ParseMode.HTML
# reply_markup = done_habit_kb()


# если ответ "да"
 
done_habit = f"Отлично! 🎉\n"
f"Вы справились — молодец! 💪\n\n"

f"Ваш прогресс по привычке <b>Привычка1</b> составляет <b>X</b>%"


# если ответ "нет"
not_done_habit = f"К сожалению, привычка не была выполнена — текущая серия прервана.\n"
f"Ваш прогресс по привычке <b>Привычка1</b> составляет <b>0</b>%\n\n"

f"Продолжай стараться, и обязательно достигнешь своей цели!💫\n\n"

f"Я подготовил совет, который может помочь тебе👊\n"
# один рандомновыбранный из списка совет
