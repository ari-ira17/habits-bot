from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

choose_habit_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="По дням", callback_data="by_day"),
        InlineKeyboardButton(text="По неделям", callback_data="by_week"),
    ],
    [
        InlineKeyboardButton(text="Пока не создавать", callback_data="no")
    ]
])