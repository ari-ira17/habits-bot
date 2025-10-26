# всякое подключение
all = ("router",)

from aiogram import Router

from .habit_by_day import router as habit_by_day_router
from .scheduler import router as scheduler_router

router = Router(name=__name__)

router.include_router(habit_by_day_router)
router.include_router(scheduler_router)