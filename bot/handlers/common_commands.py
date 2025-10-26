from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from keyboards.inline_keyboards.choose_habit_kb import get_on_start_kb

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        text = f"Приветствую тебя, {message.from_user.full_name}!\n"
                f"Я - HabitsBot, помогающий формировать полезные привычки!\n\n"
                f"Вот что я умею:\n"
                f"• Создавать привычки\n"
                f"• Напоминать о них\n"
                f"• Отслеживать прогресс\n\n"
                f"Начнем?",
        reply_markup=get_on_start_kb(),
    )