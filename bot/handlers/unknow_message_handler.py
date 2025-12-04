from aiogram import Router, types

router = Router(name=__name__)

@router.message()
async def handle_unknown_message(message: types.Message):

    await message.answer(
        text = f"Взаимодействие с ботом происходит через команды😉\n\n"
                f"Используйте /help для просмотра доступных команд🫂"
        )
    