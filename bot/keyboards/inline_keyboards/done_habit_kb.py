from aiogram.types import (
    InlineKeyboardButton
)

from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards.reply_keyboards.get_on_start_kb import ButtonText

def done_habit_kb(habit_id: int): 

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=ButtonText.YES, callback_data=f"complete_yes_{habit_id}"))
    builder.add(InlineKeyboardButton(text=ButtonText.NO, callback_data=f"complete_no_{habit_id}"))
    builder.adjust(2)
    
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
