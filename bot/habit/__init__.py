# всякое подключение
all = ("router",)

from aiogram import Router

from .add_habit import router as add_habit_router
from .habit_by_day import router as habit_by_day_router
from .habit_by_week import router as habit_by_week_router
from .scheduler import router as scheduler_router
from .timezone import router as timezone_router

router = Router(name=__name__)

router.include_router(add_habit_router)
router.include_router(habit_by_day_router)
router.include_router(habit_by_week_router)
router.include_router(scheduler_router)
router.include_router(timezone_router)
