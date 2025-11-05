from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from keyboards.reply_keyboards.done_habit_kb import ButtonText
from keyboards.inline_keyboards.choose_habit_kb import choose_habit_kb
from .data import user_habits


router = Router(name=__name__)


async def show_examples_of_habits(message: types.Message):
    await message.answer(
        text = f"Вы можете создать привычку с разным типом повторения:\n\n"  
    )
    await message.answer(
        text = f"📚  Привычка <b>Чтение</b> с напоминанием каждые 2 дня в 20:00\n"
                f"🧹  Привычка <b>Уборка</b> с напоминанием по вторникам каждые две недели в 10:00\n\n"
                f"Хотите создать задачу с повторением по дням или по неделям?",
                reply_markup=choose_habit_kb,             
    )


@router.message(Command("add_habit"))
async def timezone_check(message: types.Message, state : FSMContext):

    user_id = message.from_user.id

    if user_id not in user_habits:
        from .timezone import ask_timezone
        await ask_timezone(message, state)
        return
    await show_examples_of_habits(message)


@router.callback_query(F.data=="no")
async def add_habit_no(callback: types.CallbackQuery):
    await callback.message.answer(
        text= f"Если появится желание - используйте команду /add_habit😌",
    )
    