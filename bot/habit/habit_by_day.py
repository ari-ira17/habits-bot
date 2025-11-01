#обработка привычки с повтором, например, каждые 2 дня

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils import markdown
from aiogram.enums import ParseMode

from .states import Habit_By_Days
from .data import user_habits

router = Router(name=__name__)

@router.callback_query(F.data=="by_day")
async def add_habit_by_day(callback: types.CallbackQuery, state : FSMContext):
    await state.set_state(Habit_By_Days.title)

    await state.update_data(owner_id=callback.from_user.id)
    await callback.message.edit_reply_markup(reply_markup=None)

    await callback.message.answer(
        text = f"Введите название привычки, которая " 
                f"будет повторяться по дням:"
        )
    

@router.message(Habit_By_Days.title, F.text)
async def set_num_days(message : types.Message, state : FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(Habit_By_Days.num_days)

    await message.answer(
                text = f"Введите для привычки {markdown.hbold(message.text)} "
                        f"число повторов в днях:",
                parse_mode=ParseMode.HTML,
                ) 
    

@router.message(Habit_By_Days.time_to_check, F.text)
async def set_time_to_check(message: types.Message, state: FSMContext):
    parts = message.text.split(':')

    if len(parts) == 2 and parts[0].isnumeric() and parts[1].isnumeric():
        hours = int(parts[0])
        minutes = int(parts[1])
        if (0 <= hours <= 23 and 0 <= minutes <= 59):
            await state.update_data(time_to_check=f"{hours:02d}:{minutes:02d}")

            data = await state.get_data()
            await send_habit_by_week(message, data)
            await state.clear()  
            return
        else:
            await message.answer(
                text = f"Пожалуйста, проверьте, что время удовлетворяет принятым условиям:\n"
                        f"0 ≤ ЧЧ ≤ 23, 0 ≤ ММ ≤ 59"
            )
            return
    else:
        await message.answer(
            text = "Пожалуйста, введите время напоминания о привычке в формате <b>ЧЧ:ММ</b>:",
            parse_mode=ParseMode.HTML,
        )
    return

    
@router.message(Habit_By_Days.title)
async def set_title_invalid_contetnt_type(message: types.Message):
    await message.answer(
        text = "Пожалуйста введите название привычки текстовым сообщением."
    )


@router.message(Habit_By_Days.num_days, F.text)
async def set_num_days_invalid_content_type(message: types.Message, state: FSMContext):
    num_days = message.text

    if not (num_days.isnumeric() and int(num_days) > 0):
        await message.answer(
            text = f"Число дней должно быть положительным числом. "
            f"Пожалуйста, попробуйте еще раз."
        )
        return
    else:
        await state.update_data(num_days=int(num_days))
        await state.set_state(Habit_By_Days.time_to_check)
        await message.answer(
            text = "Введите введите время напоминания о привычке в формате <b>ЧЧ:ММ</b>:",
            parse_mode=ParseMode.HTML,
        )


async def send_habit_by_week(message: types.Message, data: dict) -> None:
    user_id = message.from_user.id
    
    if user_id not in user_habits:
        user_habits[user_id] = []

    user_habits[user_id].append(data)

    text = (
        f"<b>Ваша добавленная привычка</b>:\n\n"

        f"Название: {data['title']}\n"
        f"Число повторов в днях: {data['num_days']}\n"
        f"Время напоминания: {data['time_to_check']}\n"
    )
    await message.answer(text=text, parse_mode=ParseMode.HTML,)
 
