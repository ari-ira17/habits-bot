from aiogram import Router, F, types
from aiogram.filters import Command
from sqlalchemy import select
import os
import sys

from .format_habit import format_habit_info_for_deletion

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bot'))
from models import Habit
from db import get_db

router = Router(name=__name__)


@router.message(Command("show_my_habits"))
async def cmd_show_my_habits(message: types.Message):
    user_id = message.from_user.id

    user_habits_from_db = []
    async for session in get_db():
        result = await session.execute(
            select(Habit).where(Habit.user_id == user_id)
        )
        user_habits_from_db = result.scalars().all()
        break  

    if not user_habits_from_db:
        await message.answer(
            text="У вас пока нет добавленных привычек.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return

    habit_list_text = "📋 Ваши привычки:\n\n"
    for index, habit in enumerate(user_habits_from_db, start=1):
        habit_details = await format_habit_info_for_deletion(habit)
        numbered_habit_info = f"{index}. {habit_details}"
        habit_list_text += numbered_habit_info

    full_text = "".join(habit_list_text) 
    
    await message.answer(
        text=full_text,
        reply_markup=types.ReplyKeyboardRemove()
    )
