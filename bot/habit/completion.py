from aiogram import Router, types, F
from sqlalchemy import select
import sys
import os
import logging
import random

from .scheduler import calculate_completion_percentage, deactivate_habit_if_completed

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bot'))
from models import Habit, HabitCompletion
from db import get_db
from crud import record_habit_completion
from advices import supporting_tips


router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("complete_yes_"))
async def handle_completion(callback: types.CallbackQuery):

    habit_id_str = callback.data.split("complete_yes_", 1)[1] 
    try:
        habit_id = int(habit_id_str)
    except ValueError:
        await callback.answer("Ошибка: некорректный ID привычки.", show_alert=True)
        return

    async for session in get_db():

        await record_habit_completion(
            db_session=session,
            habit_id=habit_id
        )
        
        await session.commit()
        logger.info(f"Привычка {habit_id} отмечена как выполненная.")

        result = await session.execute(select(Habit.name).where(Habit.id == habit_id))
        habit_name = result.scalar_one_or_none()

        if not habit_name:
            await callback.answer("Ошибка: привычка не найдена.", show_alert=True)
            return

        percentage = await calculate_completion_percentage(habit_id)

        done_habit = (
            f"Отлично! 🎉\n"
            f"Вы справились — молодец! 💪\n\n"
            f"Ваш прогресс по привычке <b>{habit_name}</b> составляет <b>{percentage}</b>%"
        )

        await callback.message.edit_text(text=done_habit, parse_mode='HTML', reply_markup=None)

        await deactivate_habit_if_completed(habit_id, callback.bot, callback.from_user.id, habit_name)

    await callback.answer()

@router.callback_query(F.data.startswith("complete_no_"))
async def handle_not_done(callback: types.CallbackQuery):

    habit_id_str = callback.data.split("complete_no_", 1)[1] 
    try:
        habit_id = int(habit_id_str)
    except ValueError:
        await callback.answer("Ошибка: некорректный ID привычки.", show_alert=True)
        return

    async for session in get_db():
        result = await session.execute(select(Habit.name).where(Habit.id == habit_id))
        habit_name = result.scalar_one_or_none()

        if not habit_name:
            await callback.answer("Ошибка: привычка не найдена.", show_alert=True)
            return
        
        motivation = random.choice(supporting_tips)

        not_done_habit = (
            f"К сожалению, привычка не была выполнена — текущая серия прервана.\n"
            f"Ваш прогресс по привычке <b>{habit_name}</b> составляет <b>0</b>%\n\n"
            f"Продолжай стараться, и обязательно достигнешь своей цели!💫\n\n"
            f"Я подготовил совет, который может помочь тебе👊\n"
            f"{motivation}"
        )

        await callback.message.edit_text(text=not_done_habit, parse_mode='HTML', reply_markup=None)

    await callback.answer()
