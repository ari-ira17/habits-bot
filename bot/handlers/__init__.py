all = ("router",)

from aiogram import Router

router = Router(name=__name__)

from handlers.start_handler import router as start_router
from handlers.help_handler import router as help_router
from handlers.show_habits_handler import router as show_habits_handler_router
from handlers.send_statistic import router as send_statistic_router
from handlers.add_habit_handler import router as add_habit_router
from handlers.delete_habit_handler import router as delete_habit_router
from handlers.unknow_message_handler import router as unknow_message_router

router.include_router(start_router)
router.include_router(help_router)
router.include_router(show_habits_handler_router)
router.include_router(send_statistic_router)
router.include_router(add_habit_router)
router.include_router(delete_habit_router)
router.include_router(unknow_message_router)
