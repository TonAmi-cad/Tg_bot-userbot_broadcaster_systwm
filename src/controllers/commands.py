from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.core.config import load_config

router = Router()
config = load_config('.env')
admin_ids = [int(admin['id']) for admin in config.interface_bot.admin]


def get_account_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for account in config.userbot_account.userbot_account:
        builder.add(InlineKeyboardButton(text=account['name'], callback_data=f"select_account:{account['name']}"))
    builder.adjust(1)
    return builder.as_markup()


@router.message(Command("start"))
async def start_handler(message: Message):
    if message.from_user.id in admin_ids:
        await message.answer("Выберите аккаунт для управления:", reply_markup=get_account_keyboard())
    else:
        await message.answer("У вас нет прав доступа.")

