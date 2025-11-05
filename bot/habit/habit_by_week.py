from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils import markdown
from aiogram.enums import ParseMode
from datetime import datetime, timezone

from .states import Habit_By_Week
from .data import user_habits
from .scheduler import ru_days_to_cron, habit_by_week_scheduler
from create_bot import scheduler

router = Router(name=__name__)

@router.callback_query(F.data=="by_week")
async def add_habit_by_week(callback: types.CallbackQuery, state : FSMContext):
    await state.set_state(Habit_By_Week.title)

    await state.update_data(owner_id=callback.from_user.id)
    await callback.message.edit_reply_markup(reply_markup=None)

    await callback.message.answer(
        text = f"Введите название привычки, которая " 
                f"будет повторяться по неделям:"
        )
    
@router.message(Habit_By_Week.title, F.text)
async def set_period(message: types.Message, state : FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(Habit_By_Week.period)

    await message.answer(
        text = f"Введите для привычки {markdown.hbold(message.text)} "
                f"число повторов в неделях.\n\n"

                f"🫶 Примеры:\n"
                f"Введено {markdown.hbold('«1»')} - повтор каждую неделю.\n"
                f"Введено {markdown.hbold('«2»')} - повтор каждые две недели.\n"
                f"Введено {markdown.hbold('«3»')} - повтор каждые три недели.\n"
                f"Введено {markdown.hbold('«4»')} - повтор каждый месяц.",
        parse_mode=ParseMode.HTML,
    )

@router.message(Habit_By_Week.period, F.text)
async def set_weekdays(message: types.Message, state : FSMContext):
    await state.update_data(period=message.text)
    await state.set_state(Habit_By_Week.weekdays)

    await message.answer(
        text = f"Введите дни недели, по которым будет повторяться привычка "
                f" в формате {markdown.hbold('День1, День2, День3')}.\n\n"
                
                f"🤝 Примеры:\n"
                f"Введено {markdown.hbold('«Вт»')} - повтор по вторникам\n"
                f"Введено {markdown.hbold('«Пн, Ср, Пт»')} - повтор по понедельникам, " 
                f"средам, пятницам.\n",
        parse_mode=ParseMode.HTML,
    )

@router.message(Habit_By_Week.weekdays, F.text)
async def set_weekdays_handler(message: types.Message, state: FSMContext):
    text = message.text.strip()
    input_lower = text.lower()
    
    allowed = {"пн", "вт", "ср", "чт", "пт", "сб", "вс"}
    
    parts = [part.strip() for part in input_lower.split(",") if part.strip()]
    
    invalid = [part for part in parts if part not in allowed]
    
    if invalid:
        await message.answer(
            text=(
                f"Некорректные дни: {', '.join(invalid)}.\n"
                f"Пожалуйста, введите дни недели в формате {markdown.hbold('День1, День2, День3')}.\n\n"
                f"🤝 Примеры:\n"
                f"Введено {markdown.hbold('«Вт»')} - повтор по вторникам\n"
                f"Введено {markdown.hbold('«Пн, Ср, Пт»')} - повтор по понедельникам, средам, пятницам."
            ),
            parse_mode=ParseMode.HTML,
        )
        return

    await state.update_data(weekdays=text)
    await state.set_state(Habit_By_Week.time_to_check)

    await message.answer(
        text="Введите время напоминания о привычке в формате <b>ЧЧ:ММ</b>:",
        parse_mode=ParseMode.HTML,
    )

@router.message(Habit_By_Week.time_to_check, F.text)
async def set_time_to_check(message: types.Message, state: FSMContext, bot):
    parts = message.text.split(':')

    if len(parts) == 2 and parts[0].isnumeric() and parts[1].isnumeric():
        hours = int(parts[0])
        minutes = int(parts[1])
        if (0 <= hours <= 23 and 0 <= minutes <= 59):
            await state.update_data(time_to_check=f"{hours:02d}:{minutes:02d}")

            data = await state.get_data()
            await send_habit_by_week(message, data, bot)
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

@router.message(Habit_By_Week.title)
async def set_title_invalid_contetnt_type(message: types.Message):
    await message.answer(
        text = "Пожалуйста введите название привычки текстовым сообщением."
    )


@router.message(Habit_By_Week.period, F.text)
async def set_period_invalid_content_type(message: types.Message, state: FSMContext):
    period = message.text

    if not (period.isnumeric() and int(period) > 0):
        await message.answer(
            text = f"Число неделей должно быть положительным числом. "
            f"Пожалуйста, попробуйте еще раз."
        )
        return
    else:
        await state.update_data(period=int(period))
        await state.set_state(Habit_By_Week.weekdays)
        await message.answer(
        text = f"Введите дни недели, по которым будет повторяться привычка "
                f" в формате {markdown.hbold('День1, День2, День3')}.\n\n"
                
                f"🤝 Примеры:\n"
                f"Введено {markdown.hbold('«Вт»')} - повтор по вторникам\n"
                f"Введено {markdown.hbold('«Пн, Ср, Пт»')} - повтор по понедельникам, " 
                f"средам, пятницам.\n",
        parse_mode=ParseMode.HTML,
    )


async def send_habit_by_week(message: types.Message, data: dict, bot) -> None:
    user_id = message.from_user.id

    if user_id not in user_habits:
        user_habits[user_id] = []

    data["created_at"] = datetime.now(timezone.utc).isoformat()
    user_habits[user_id].append(data)

    weekdays_display = data['weekdays']
    if isinstance(weekdays_display, list):
        weekdays_display = ", ".join(weekdays_display)

    text = (
        f"<b>Ваша добавленная привычка</b>:\n\n"
        f"Название: {data['title']}\n"
        f"Число повторов в неделях: {data['period']}\n"
        f"Дни напоминания: {weekdays_display}\n"
        f"Время напоминания: {data['time_to_check']}\n"
    )
    await message.answer(text=text, parse_mode=ParseMode.HTML)

    hours, minutes = map(int, data['time_to_check'].split(':'))
    weekdays_cron = ru_days_to_cron(data['weekdays'])
    user_timezone_str = "UTC"  

    success = await habit_by_week_scheduler(
        scheduler=scheduler,
        bot=bot,
        user_id=user_id,
        title=data['title'],
        hours=hours,
        minutes=minutes,
        weekdays_cron=weekdays_cron,
        period_weeks=int(data['period']),
        user_timezone_str=user_timezone_str,
        created_at_iso=data["created_at"]
    )

    if success:
        await message.answer(
            text = f"Напоминание успешно установлено!🥳\n\n"
                    f"Чтобы добавить новую привычку используйте /add_habit🫶"
            )
    else:
        await message.answer(
            text = f"Привычка с таким названием уже существует. "
                    f"Напоминание не установлено.")
    