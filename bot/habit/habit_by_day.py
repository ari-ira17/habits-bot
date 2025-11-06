#обработка привычки с повтором, например, каждые 2 дня

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils import markdown
from aiogram.enums import ParseMode

from .states import Habit_By_Days
from .data import user_habits
from .scheduler import habit_by_day_scheduler
from create_bot import scheduler

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
async def set_time_to_check(message: types.Message, state: FSMContext, bot):
    parts = message.text.split(':')

    if len(parts) == 2 and parts[0].isnumeric() and parts[1].isnumeric():
        hours = int(parts[0])
        minutes = int(parts[1])
        if (0 <= hours <= 23 and 0 <= minutes <= 59):
            await state.update_data(time_to_check=f"{hours:02d}:{minutes:02d}")

            data = await state.get_data()
            #await send_habit_by_day(message, data, bot)
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

# скорее всего не нужно

# bot/routers/habits_by_days.py
# from bot.db import get_db
# from bot.crud import create_habit, get_or_create_user
# from datetime import datetime
# import pytz


# async def send_habit_by_day(message: types.Message, data: dict, bot) -> None:
#     user_id = message.from_user.id

#     # Получаем сессию
#     async for session in get_db():
#         # Создаём пользователя в БД, если его нет
#         user = await get_or_create_user(db=session, telegram_id=user_id)

#         # Используем timezone_offset из БД (он должен быть в UTC, если хранится в секундах)
#         user_timezone_offset = user.timezone_offset or 0  # по умолчанию 0 (UTC)
#         user_tz = pytz.FixedOffset(user_timezone_offset // 60)  # в минутах
#         utc_tz = pytz.utc

#         # Время напоминания по локальному времени пользователя
#         hours, minutes = map(int, data['time_to_check'].split(':'))

#         # Создаём объект datetime в локальном времени пользователя
#         local_dt = datetime.now(user_tz).replace(hour=hours, minute=minutes, second=0, microsecond=0)
#         # Переводим в UTC
#         utc_dt = local_dt.astimezone(utc_tz)

#         # Пример конфига для БД
#         reminder_config = {
#             "type": "by_day",
#             "num_days": data['num_days'],
#             "time": data['time_to_check']
#         }

#         # Создаём запись в БД
#         habit = await create_habit(
#             db=session,
#             user_id=user_id,
#             name=data['title'],
#             reminder_config=reminder_config,
#             next_reminder_datetime_utc=utc_dt
#         )

#     # Сообщаем пользователю, что привычка добавлена
#     text = (
#         f"<b>Ваша добавленная привычка</b>:\n\n"
#         f"Название: {data['title']}\n"
#         f"Число повторов в днях: {data['num_days']}\n"
#         f"Время напоминания: {data['time_to_check']}\n"
#     )
#     await message.answer(text=text, parse_mode=ParseMode.HTML)

#     # Получаем таймзону из БД (если нужно для планировщика)
#     user_timezone_str = str(user_tz)  # или можно хранить в БД строкой и использовать её

#     success = await habit_by_day_scheduler(
#         scheduler=scheduler,
#         bot=bot,
#         user_id=user_id,
#         title=data['title'],
#         hours=hours,
#         minutes=minutes,
#         num_days=data['num_days'],
#         user_timezone_str=user_timezone_str
#     )

#     if success:
#         await message.answer(
#             text=f"Напоминание успешно установлено!🥳\n\n"
#                  f"Чтобы добавить новую привычку используйте /add_habit🫶"
#         )
#     else:
#         await message.answer(
#             text=f"Привычка с таким названием уже существует☹️\n\n"
#                  f"Напоминание не было установлено, создайте задачу с другим заголовком😉\n\n"
#                  f"Чтобы добавить новую привычку используйте /add_habit🫶"
#         )

# async def send_habit_by_day(message: types.Message, data: dict, bot) -> None:
#     user_id = message.from_user.id

#     if user_id not in user_habits:
#         user_habits[user_id] = []

#     user_habits[user_id].append(data)

#     text = (
#         f"<b>Ваша добавленная привычка</b>:\n\n"

#         f"Название: {data['title']}\n"
#         f"Число повторов в днях: {data['num_days']}\n"
#         f"Время напоминания: {data['time_to_check']}\n"
#     )
#     await message.answer(text=text, parse_mode=ParseMode.HTML,)

#     hours, minutes = map(int, data['time_to_check'].split(':'))

#     user_timezone_str = "UTC"  
#     user_data_list = user_habits.get(user_id, [])
#     for item in user_data_list:
#         if isinstance(item, dict) and 'timezone' in item:
#             user_timezone_str = item['timezone']
#             break

#     success = await habit_by_day_scheduler(
#         scheduler=scheduler,
#         bot=bot,
#         user_id=user_id,
#         title=data['title'],
#         hours=hours,       
#         minutes=minutes,    
#         num_days=data['num_days'],
#         user_timezone_str=user_timezone_str
#     )

#     if success:
#         await message.answer(
#             text = f"Напоминание успешно установлено!🥳\n\n"

#                     f"Чтобы добавить новую привычку используйте /add_habit🫶"
#             )
#     else:
#         await message.answer(
#             text = f"Привычка с таким названием уже существует☹️\n\n"

#                     f"Напоминание не было установлено, создайте задачу с другим заголовком😉\n\n"

#                     f"Чтобы добавить новую привычку используйте /add_habit🫶"
#             )
