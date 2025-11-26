from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
import requests 
import time
from typing import Union
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import sys

from config import CONFIG
from keyboards.reply_keyboards.get_on_start_kb import ButtonText
from .states import AskLocation

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bot'))
from db import get_db
from crud import get_or_create_user

from sqlalchemy import select
from models import User


router = Router(name=__name__)

@router.message(F.text==ButtonText.YES)
async def ask_timezone(message: types.Message, state: FSMContext):

    from .add_habit import show_examples_of_habits
    
    async for session in get_db():
        result = await session.execute(select(User.id).where(User.id == message.from_user.id))
        existing_user_id = result.scalar_one_or_none()

        if existing_user_id:
            await show_examples_of_habits(message)
            return  
        
    await state.set_state(AskLocation.waiting_for_location)
    await message.answer(
        text = f"Пожалуйста, отправьте Вашу геолокацию, "
                f"чтобы я знал, когда отправлять Вам напоминания🤝",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(AskLocation.waiting_for_location, F.location)
async def handle_location(message: types.Message, state: FSMContext):

    lat = message.location.latitude
    lon = message.location.longitude

    timezone_name = get_timezone_by_coords(lat, lon)

    if timezone_name:
        await message.answer(f"Ваш часовой пояс: {timezone_name}🌏")

        try:
            print(f"Получен timezone_name: {repr(timezone_name)}")
            tz = ZoneInfo(timezone_name)
            now = datetime.now(tz)
            offset_seconds = int(tz.utcoffset(now).total_seconds())
        except Exception as e:
            print(f"Ошибка при вычислении смещения: {e}")
            await message.answer("Не удалось вычислить смещение. Попробуйте ещё раз☹️")
            return
        
        async for session in get_db():
            user = await get_or_create_user(
                db=session,
                telegram_id=message.from_user.id,
                timezone_offset=offset_seconds
            )

        from .add_habit import show_examples_of_habits
        await show_examples_of_habits(message)

    else:
        await message.answer("Не удалось определить часовой пояс. Попробуйте ещё раз☹️")


def get_timezone_by_coords(lat: float, lon: float) -> Union[str, None]:

    api_key = CONFIG.TIMEZONEDB_API_KEY
    timestamp = int(time.time())
    url = f"https://api.timezonedb.com/v2/get-time-zone?key={api_key}&format=json&by=position&lat={lat}&lng={lon}&timestamp={timestamp}"

    try:
        response = requests.get(url)
        data = response.json()
        if data.get('status') == 'OK':
            return data['zoneName']        
        else:
            print(f"Ошибка от API: {data.get('message')}")
            return None
    except Exception as e:
        print(f"Ошибка при получении часового пояса: {e}")
        return None
