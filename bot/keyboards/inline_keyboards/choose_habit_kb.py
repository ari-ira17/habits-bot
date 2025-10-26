# кнопки “по дням”, “по неделям”, “нет”

from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder

class ButtonText:
    YES = "Да!"
    NO = "Нет."

def get_on_start_kb() -> ReplyKeyboardMarkup:
    button_yes = KeyboardButton(text=ButtonText.YES)
    button_no = KeyboardButton(text=ButtonText.NO)
    buttons_first_row = [button_yes, button_no]
    markup = ReplyKeyboardMarkup(
        keyboard=[buttons_first_row],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return markup

#после старта сделать кнопки помощь, нет, добавить привычку
# далее кнопки по дням по неделям 