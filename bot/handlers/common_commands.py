from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove
from sqlalchemy import select, delete
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import os
import sys

from keyboards.reply_keyboards.get_on_start_kb import get_on_start_kb, ButtonText
from keyboards.inline_keyboards.confirm_delete_habit_kb import confirm_delete_kb

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bot'))
from models import Habit, HabitCompletion
from db import get_db

sys.path.append(os.path.dirname(os.path.abspath(__file__)))    
from habit.scheduler import calculate_completion_percentage

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        text = f"Приветствую Вас, {message.from_user.full_name}!\n\n"
                f"Я - <b>HabitsBot</b>, помогающий формировать полезные привычки😌\n\n"
                f"С моей помощью Вы можете <b>создать задачу</b>, о которой я буду <b>напоминать</b> в заданное время, "
                f"а также каждую неделю Вы начнете получать <b>отчет со статистикой</b> выполнения каждой привычки🤝\n\n"
                f"Вот мои <b>команды</b>:\n"
                f"- /help - общая информация (возможности бота, сбор статистики, принципы формирования привычек, обратная связь)\n"
                f"- /show_my_habits - покажет все Ваши созданные привычки\n"
                f"- /add_habit - добавление новой привычки\n\n"
                f"Начнем?🦾",
        reply_markup=get_on_start_kb(),
    )


@router.message(F.text == ButtonText.NO)
async def stop_bot(message: types.Message):
    await message.answer(
        text = f"Возвращайтесь, когда будете готовы создать свою первую привычку. "
                f"Я всегда здесь чтобы помочь!\n\n"
                f"Чтобы начать позже, просто используйте команду /add_habit😊",
                reply_markup=ReplyKeyboardRemove()) 
    
    
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        text = f"Приветствую Вас, {message.from_user.full_name}!\n\n"
                f"Я - <b>HabitsBot</b>, помогающий формировать полезные привычки😌\n\n"

                f"С моей помощью Вы можете <b>создать задачу</b>, о которой я буду <b>напоминать</b> в заданное время, "
                f"а также каждую неделю Вы начнете получать <b>отчет со статистикой</b> выполнения каждой привычки🤝\n\n"

                f"Вот мои <b>команды</b>:\n"
                f"- /help - общая информация (возможности бота, сбор статистики, принципы формирования привычек, обратная связь)\n"
                f"- /add_habit - добавление новой привычки\n"
                f"- /delete_habit - удалит выбранную привычку\n"
                f"- /send_statistic - покажет статистику по привычкам\n"
                f"- /show_my_habits - покажет все Ваши созданные привычки\n\n"

                f"Процесс формирования привычки основан на <b>многократном выполнении</b> привычки, " 
                f"чем осуществляется ее закрепление. "
                f"Вы можете создать привычку с разным типом повторения:\n\n"

                f"📚  Привычка <b>Чтение</b> с напоминанием каждые 2 дня в 20:00\n"
                f"🧹  Привычка <b>Уборка</b> с напоминанием по вторникам каждые две недели в 10:00\n\n"

                f"Когда приходит время <b>напомнить о задаче</b>, я присылаю уведомление, " 
                f"а Вам нужно <b>ответить</b>, выполнили ли Вы ее✅\n\n"

                f"В случае <b>отрицательного ответа</b> процент выполнения привычки <b>обнуляется</b>, "
                f"и я пришлю <b>совет</b> по ее успешному формированию🫂\n\n"

                f"Также еженедельно Вы получаете <b>отчет</b>, который покажет Вам, "
                f"насколько Вы <b>близки</b> к формированию каждой привычки " 
                f"с помощью детальной <b>статистики</b> и визуального прогресса!✨\n\n"

                f"P.S. По всем возникающим вопросам можете <b>обратиться</b> к разработчику - @ari_ira17👩‍💻",
        reply_markup=ReplyKeyboardRemove()
    )


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


async def format_habit_info_for_deletion(habit: Habit) -> str:

    percentage = await calculate_completion_percentage(habit.id)


    config = habit.reminder_config
    habit_type = config.get("type", "неизвестно")

    habit_info_lines = [
        f"Название: <b>{habit.name}</b>"
    ]

    if habit_type == "by_days":
        habit_info_lines.append(f"Тип: повторение каждые {config.get('num_days', '?')} день(а)")
        habit_info_lines.append(f"Время напоминания: {config.get('time_to_check', '?')}")

    elif habit_type == "by_week":
        period = config.get('period_weeks', '?')
        days = config.get('weekdays', [])
        time_check = config.get('time_to_check', '?')
        days_str = ", ".join(days) if days else "?"
        habit_info_lines.append(f"Тип: повторение каждые {period} недель(и)")
        habit_info_lines.append(f"Дни напоминания: {days_str}")
        habit_info_lines.append(f"Время напоминания: {time_check}")

    status = "✅ Активна" if habit.is_active else "❌ Неактивна"
    habit_info_lines.append(f"Статус: {status}")
    habit_info_lines.append(f"Процент выполнения: {percentage}%")

    habit_info = "\n".join(habit_info_lines) + "\n\n"
    return habit_info
