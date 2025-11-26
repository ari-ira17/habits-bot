from aiogram import Router, types
from aiogram.filters import Command
from .generate_statistic import generate_statistic_image

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bot'))
from db import get_db


router = Router(name=__name__)

@router.message(Command("send_statistic"))
async def send_statistic(message: types.Message):
    user_id = message.from_user.id

    async for session in get_db():
        image_bytes = await generate_statistic_image(user_id, session)

    await message.answer_photo(
        photo=types.BufferedInputFile(
            image_bytes.read(),
            filename="statistic.png"
        ),
        caption="📊 Ваш отчёт по привычкам!"
    )
    