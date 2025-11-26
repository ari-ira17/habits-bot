from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

class ButtonText:
    CANCEL_DELETION = "❌ Отменить"

def confirm_delete_kb() -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()
    builder.button(
        text=ButtonText.CANCEL_DELETION,
        callback_data="cancel_delete_habit_process" 
    )
    return builder.as_markup(resize_keyboard=True)
