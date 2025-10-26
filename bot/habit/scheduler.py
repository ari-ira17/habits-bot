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
