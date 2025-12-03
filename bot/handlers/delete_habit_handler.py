from aiogram import Router, F, types
from aiogram.filters import Command
from sqlalchemy import select, delete
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import os
import sys

from keyboards.inline_keyboards.confirm_delete_habit_kb import confirm_delete_kb
from .format_habit import format_habit_info_for_deletion

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bot'))
from models import Habit, HabitCompletion
from db import get_db


router = Router(name=__name__)

class DeleteHabit(StatesGroup):
    waiting_for_habit_number = State()


@router.message(Command("delete_habit"))
async def cmd_delete_habit(message: types.Message, state: FSMContext):

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
            text="У вас нет добавленных привычек для удаления🧐",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return

    habit_list_text = "📋 Ваши привычки:\n\n"
    for index, habit in enumerate(user_habits_from_db, start=1):
        habit_details = await format_habit_info_for_deletion(habit)
        numbered_habit_info = f"{index}. {habit_details}"
        habit_list_text += numbered_habit_info

    habit_list_text += "\nПожалуйста, введите номер привычки, которую хотите удалить (или нажмите кнопку для отмены)😉"    

    await message.answer(
        text=habit_list_text,
        parse_mode='HTML',
        reply_markup=confirm_delete_kb() 
    )

    await state.set_state(DeleteHabit.waiting_for_habit_number)
    await state.update_data(user_habits_list=user_habits_from_db)


@router.callback_query(F.data == "cancel_delete_habit_process", DeleteHabit.waiting_for_habit_number)
async def handle_cancel_delete_via_button(callback: types.CallbackQuery, state: FSMContext):

    await callback.message.edit_text(
        text="Операция удаления привычки отменена🥰",
        parse_mode='HTML',
    )

    await callback.answer()


@router.message(DeleteHabit.waiting_for_habit_number, F.text)
async def process_habit_number(message: types.Message, state: FSMContext):

    user_input = message.text.strip()

    if not user_input.isdigit():
        await message.answer("Пожалуйста, введите корректный номер привычки (цифру)😇")
        return

    habit_index = int(user_input) - 1

    data = await state.get_data()
    user_habits_list = data.get("user_habits_list", [])

    if habit_index < 0 or habit_index >= len(user_habits_list):
        await message.answer("Номер привычки вне диапазона. Попробуйте снова😇")
        return

    selected_habit = user_habits_list[habit_index]
    selected_habit_id = selected_habit.id
    selected_habit_name = selected_habit.name

    user_id = message.from_user.id
    success = False
    async for session in get_db():

        result = await session.execute(
            select(Habit).where(Habit.id == selected_habit_id, Habit.user_id == user_id)
        )
        habit_to_delete = result.scalar_one_or_none()

        if not habit_to_delete:
            await message.answer("Ошибка: привычка не найдена или не принадлежит Вам🧐")
            await state.clear()
            return

        await session.execute(
            delete(HabitCompletion).where(HabitCompletion.habit_id == selected_habit_id)
        )
        await session.delete(habit_to_delete)
        await session.commit()
        success = True
        break 

    if success:
        await message.answer(f"Привычка \"<b>{selected_habit_name}</b>\" успешно удалена", parse_mode='HTML')
    else:
        await message.answer("Ошибка при удалении привычки")

    await state.clear()
