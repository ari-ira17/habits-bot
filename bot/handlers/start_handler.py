from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove

from keyboards.reply_keyboards.get_on_start_kb import get_on_start_kb, ButtonText

router = Router(name=__name__)


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        text = f"Приветствую Вас, {message.from_user.full_name}!\n\n"
                f"Я - <b>HabitsBot</b>, помогающий формировать полезные привычки😌\n\n"
                f"С моей помощью Вы можете <b>создать задачу</b>, о которой я буду <b>напоминать</b> в заданное время, "
                f"а также каждую неделю Вы начнете получать <b>отчет со статистикой</b> выполнения каждой привычки🤝\n\n"
                f"Вот мои <b>команды</b>:\n"
                f"- /help - общая информация (возможности бота, сбор статистики, принципы формирования привычек, обратная связь)\n"
                f"- /show_my_habits - покажет все Ваши созданные привычки\n"
                f"- /add_habit - добавление новой привычки\n\n"
                f"Начнем?🦾",
        reply_markup=get_on_start_kb(),
    )


@router.message(F.text == ButtonText.NO)
async def stop_bot(message: types.Message):
    await message.answer(
        text = f"Возвращайтесь, когда будете готовы создать свою первую привычку. "
                f"Я всегда здесь чтобы помочь!\n\n"
                f"Чтобы начать позже, просто используйте команду /add_habit😊",
                reply_markup=ReplyKeyboardRemove()) 