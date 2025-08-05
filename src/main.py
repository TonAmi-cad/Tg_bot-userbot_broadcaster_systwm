import sys
import os
import asyncio
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, Message as AiogramMessage
from pyrogram import Client, filters
from pyrogram.types import Message as PyrogramMessage

from src.core.config import load_config
from src.controllers import commands, admin_commands
from src.core.userbot import UserBot

logging.basicConfig(level=logging.INFO)
config = load_config('.txt')
admin_ids = [int(admin['id']) for admin in config.interface_bot.admin]

async def set_bot_commands(bot: Bot):
    commands_list = [BotCommand(command="/start", description="Запустить бота")]
    await bot.set_my_commands(commands_list)

def register_userbot_handlers(userbot: UserBot, bot_username: str):
    @userbot.client.on_message(filters.private & ~filters.me)
    async def new_message_handler(client: Client, message: PyrogramMessage):
        sender_id = message.from_user.id
        sender_name = message.from_user.first_name
        
        # Формируем текст для отправки основному боту
        text_to_forward = f"{userbot.account['name']}::{sender_id}::{sender_name}::{message.text}"
        
        # Отправляем сообщение основному боту
        await client.send_message(bot_username, text_to_forward)

# Обработчик сообщений, пришедших от юзерботов
async def message_from_userbot_handler(message: AiogramMessage, bot: Bot):
    try:
        userbot_name, sender_id, sender_name, user_message = message.text.split('::', 3)
        sender_id = int(sender_id)

        # Сообщение, которое увидит админ
        admin_message_text = (
            f"📨 <b>Кому:</b> {userbot_name}\n"
            f"👤 <b>От кого:</b> {sender_name}\n\n"
            f"<i>Текст сообщения:</i>\n{user_message}\n\n"
            f"<code>{sender_id}:{userbot_name}</code>"
        )

        for admin_id in admin_ids:
            # Отправляем админу единое сообщение
            await bot.send_message(
                chat_id=admin_id,
                text=admin_message_text,
                parse_mode="HTML"
            )
    except ValueError:
        # Если сообщение от юзербота пришло в неверном формате
        logging.warning(f"Получено сообщение в неверном формате от юзербота: {message.text}")


async def main():
    bot = Bot(token=config.interface_bot.token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    await set_bot_commands(bot)

    dp.include_router(commands.router)
    dp.include_router(admin_commands.router)
    
    userbots = {account['name']: UserBot(account) for account in config.userbot_account.userbot_account}
    dp['userbots'] = userbots

    bot_username = config.interface_bot.username
    for userbot in userbots.values():
        await userbot.start()
        register_userbot_handlers(userbot, bot_username)
        logging.info(f"Userbot {userbot.account['name']} started")

    # Получаем ID юзерботов ПОСЛЕ их запуска
    userbot_ids = [userbot.client.me.id for userbot in userbots.values()]

    # Регистрируем обработчик для сообщений от юзерботов
    dp.message.register(message_from_userbot_handler, F.from_user.id.in_(userbot_ids))

    try:
        await dp.start_polling(bot)
    finally:
        for userbot in userbots.values():
            await userbot.stop()
            logging.info(f"Userbot {userbot.account['name']} stopped")

if __name__ == "__main__":
    asyncio.run(main())
