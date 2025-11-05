from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
import requests 
import time
from typing import Union

from .data import user_habits
from config import CONFIG
from keyboards.reply_keyboards.done_habit_kb import ButtonText
from .states import AskLocation
from .add_habit import show_examples_of_habits


router = Router(name=__name__)

@router.message(F.text==ButtonText.YES)
async def ask_timezone(message: types.Message, state: FSMContext):
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
        if message.from_user.id not in user_habits:
            user_habits[message.from_user.id] = []
        user_habits[message.from_user.id].append({'timezone': timezone_name})

        await message.answer(f"Ваш часовой пояс: {timezone_name}.")
        await show_examples_of_habits(message)
    else:
        await message.answer("Не удалось определить часовой пояс. Попробуйте ещё раз.")


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
