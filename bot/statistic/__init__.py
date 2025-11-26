all = ("router",)

from aiogram import Router
from .send_statistic import router as send_statistic_router

router = Router(name=__name__)

router.include_router(send_statistic_router)