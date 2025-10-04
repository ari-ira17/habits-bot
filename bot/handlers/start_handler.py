from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

start_router = Router()


@start_router.message(CommandStart())
async def cmd_start(message: Message):
    print(message.from_user.id)
    await message.answer(f'Приветствую тебя, {message.from_user.first_name}')
        