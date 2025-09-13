import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, Message as AiogramMessage
from pyrogram import Client, filters
from pyrogram.types import Message as PyrogramMessage

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.controllers.admin_commands import admin_router
from src.controllers.debug_commands import router as debug_router
from src.core.dependencies import (
    mailing_service,
    config,
    admin_ids,
    database,
)
from src.core.scheduler import setup_scheduler
from src.core.userbot import UserBot
from src.models.models import Base

logging.basicConfig(level=logging.INFO)

# Глобальные переменные для планировщика
_global_bot = None
_global_userbots = None





def init_db():
    """Инициализирует базу данных и создает таблицы."""
    with database.engine.begin() as conn:
        Base.metadata.create_all(conn)


async def set_bot_commands(bot: Bot):
    commands_list = [
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/create_mailing", description="Создать новую рассылку"),
        BotCommand(command="/edit_mailing", description="Редактировать рассылку"),
    ]
    if config.debug.debug_flag:
        commands_list.append(BotCommand(command="/debug_mail", description="Отладка рассылок"))
    await bot.set_my_commands(commands_list)


def register_userbot_handlers(userbot: UserBot, bot_username: str):
    @userbot.client.on_message(filters.private & ~filters.me)
    async def new_message_handler(client: Client, message: PyrogramMessage):
        sender_id = message.from_user.id
        sender_name = message.from_user.first_name
        text_to_forward = (
            f"{userbot.account['name']}::{sender_id}::{sender_name}::{message.text}"
        )
        await client.send_message(bot_username, text_to_forward)


async def message_from_userbot_handler(message: AiogramMessage, bot: Bot):
    try:
        userbot_name, sender_id, sender_name, user_message = message.text.split("::", 3)
        sender_id = int(sender_id)

        admin_message_text = (
            f"📨 <b>Кому:</b> {userbot_name}\n"
            f"👤 <b>От кого:</b> {sender_name}\n\n"
            f"<i>Текст сообщения:</i>\n{user_message}\n\n"
            f"<code>{sender_id}:{userbot_name}</code>"
        )

        for admin_id in admin_ids:
            await bot.send_message(
                chat_id=admin_id, text=admin_message_text, parse_mode="HTML"
            )
    except ValueError:
        logging.warning(
            f"Получено сообщение в неверном формате от юзербота: {message.text}"
        )


async def on_startup(bot: Bot, **kwargs):
    """Выполняется при запуске бота."""
    # Получаем dispatcher из kwargs или из глобального контекста
    dp = kwargs.get('dispatcher')
    if not dp:
        # Если dispatcher не передан в kwargs, получаем его из bot
        dp = bot.dispatcher if hasattr(bot, 'dispatcher') else None
        if not dp:
            logging.error("Не удалось получить dispatcher в on_startup")
            return
    
    await set_bot_commands(bot)
    
    bot_username = config.interface_bot.username
    userbots = dp.get("userbots")
    for userbot in userbots.values():
        await userbot.start()
        if userbot.client:
            register_userbot_handlers(userbot, bot_username)
            logging.info(f"Userbot {userbot.account['name']} started")
        else:
            logging.warning(
                f"Userbot {userbot.account['name']} failed to start and will be skipped."
            )

    userbot_ids = []
    for userbot in userbots.values():
        if userbot and userbot.client and userbot.client.is_connected:
            user_me = await userbot.client.get_me()
            userbot_ids.append(user_me.id)

    if userbot_ids:
        dp.message.register(
            message_from_userbot_handler, F.from_user.id.in_(userbot_ids)
        )

    # Прогреваем peer-кеш у каждого юзербота, чтобы избежать Peer id invalid
    try:
        active_mailings = mailing_service.get_active_mailings()
    except Exception:
        active_mailings = []

    # Если активных нет, возьмём все для прогрева
    try:
        all_mailings = mailing_service.get_all_mailings()
    except Exception:
        all_mailings = []

    mailings_to_warm = active_mailings or all_mailings

    for userbot in userbots.values():
        if not userbot.client or not userbot.client.is_connected:
            continue
        # Диалоги (прогрев peer-кеша). В некоторых версиях Pyrogram get_dialogs
        # может быть асинхронным генератором. Используем iter_dialogs() как
        # совместимый способ и читаем хотя бы один элемент.
        try:
            # Pyrogram v2+ использует get_dialogs
            if hasattr(userbot.client, "get_dialogs"):
                async for _ in userbot.client.get_dialogs():
                    break
            # Pyrogram v1 использовал iter_dialogs
            elif hasattr(userbot.client, "iter_dialogs"):
                async for _ in userbot.client.iter_dialogs():
                    break
        except Exception as e:
            logging.warning(f"Не удалось получить диалоги для {userbot.account['name']}: {e}")

        # Резолвим чаты из рассылок
        for mailing in mailings_to_warm:
            if mailing.userbot_name != userbot.account['name']:
                continue
            for chat in mailing.chat_ids:
                candidates = []
                try:
                    as_int = int(chat)
                    candidates.append(as_int)
                    if as_int < -1000 and not str(as_int).startswith("-100"):
                        candidates.append(int("-100" + str(abs(as_int))))
                except Exception:
                    candidates.append(chat)

                for candidate in candidates:
                    try:
                        try:
                            await userbot.client.resolve_peer(candidate)
                        except Exception:
                            await userbot.client.get_chat(candidate)
                        break
                    except Exception:
                        continue

    scheduler = setup_scheduler(userbots, bot)
    dp["scheduler"] = scheduler


async def on_shutdown(dp: Dispatcher):
    """Выполняется при выключении бота."""
    scheduler = dp.get("scheduler")
    if scheduler:
        scheduler.shutdown()

    userbots = dp.get("userbots")
    if userbots:
        for userbot in userbots.values():
            await userbot.stop()
            logging.info(f"Userbot {userbot.account['name']} stopped")


async def main():
    bot = Bot(token=config.interface_bot.token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    userbots = {
        account["name"]: UserBot(account)
        for account in config.userbot_account.userbot_account
    }

    # Устанавливаем глобальные переменные
    global _global_bot, _global_userbots
    _global_bot = bot
    _global_userbots = userbots

    dp.include_router(admin_router)
    if config.debug.debug_flag:
        dp.include_router(debug_router)

    dp["userbots"] = userbots
    dp["mailing_service"] = mailing_service
    dp["admin_ids"] = admin_ids
    dp["config"] = config

    async def startup_wrapper(bot: Bot):
        await on_startup(bot, dispatcher=dp)
    
    async def shutdown_wrapper():
        await on_shutdown(dp)
    
    dp.startup.register(startup_wrapper)
    dp.shutdown.register(shutdown_wrapper)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    init_db()
    asyncio.run(main())
