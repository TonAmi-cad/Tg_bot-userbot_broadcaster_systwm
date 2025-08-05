import sys
import os
import asyncio
import logging

# Добавляем корневую директорию проекта в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pyrogram import Client, filters
from pyrogram.types import Message as PyrogramMessage

from src.core.config import load_config
from src.controllers import commands, admin_commands
from src.core.userbot import UserBot

logging.basicConfig(level=logging.INFO)
config = load_config('.env')
admin_ids = [int(admin['id']) for admin in config.interface_bot.admin]


async def set_bot_commands(bot: Bot):
    commands_list = [BotCommand(command="/start", description="Запустить бота")]
    await bot.set_my_commands(commands_list)


def get_reply_keyboard(userbot_name: str, user_id: int) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Ответить", callback_data=f"reply:{userbot_name}:{user_id}"))
    return builder.as_markup()


def register_userbot_handlers(userbot: UserBot, bot: Bot):
    @userbot.client.on_message(filters.private & ~filters.me)
    async def new_message_handler(client: Client, message: PyrogramMessage):
        userbot_name = userbot.account['name']
        sender_name = message.from_user.first_name
        sender_id = message.from_user.id
        text = f"Новое сообщение для {userbot_name} от {sender_name}:\n\n{message.text}"
        
        for admin_id in admin_ids:
            await bot.send_message(
                admin_id, 
                text, 
                reply_markup=get_reply_keyboard(userbot_name, sender_id)
            )


async def main():
    bot = Bot(token=config.interface_bot.token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    await set_bot_commands(bot)

    dp.include_router(commands.router)
    dp.include_router(admin_commands.router)

    userbots = {account['name']: UserBot(account) for account in config.userbot_account.userbot_account}
    dp['userbots'] = userbots

    for userbot in userbots.values():
        register_userbot_handlers(userbot, bot)
        await userbot.start()
        logging.info(f"Userbot {userbot.account['name']} started")

    try:
        await dp.start_polling(bot)
    finally:
        for userbot in userbots.values():
            await userbot.stop()
            logging.info(f"Userbot {userbot.account['name']} stopped")


if __name__ == "__main__":
    asyncio.run(main())
