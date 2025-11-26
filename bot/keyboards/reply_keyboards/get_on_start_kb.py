from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup
)


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
