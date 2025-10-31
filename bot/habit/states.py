# поля привычек, которые потом идут в БД

from aiogram.fsm.state import StatesGroup, State

class Habit_By_Week(StatesGroup):
    #habit_id = State()
    owner_id = State()
    title = State()
    status = 0
    period = State()
    weekdays = State()
    time_to_check = State()


class Habit_By_Days(StatesGroup):
    #habit_id = State()
    owner_id = State()
    title = State()
    status = 0
    num_days = State()
    time_to_check = State()