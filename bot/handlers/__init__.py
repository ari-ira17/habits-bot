all = ("router",)

from aiogram import Router

from handlers.common_commands import router as start_router
#from .habit_handler import router as habit_router

router = Router(name=__name__)

router.include_router(start_router)
#router.include_router(habit_router)