import logging
import os
import asyncio

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from src.core.dependencies import admin_ids, mailing_service
from pyrogram.types import InputMediaPhoto, InputMediaVideo
from src.models.models import Mailing
from src.views.keyboards.inline_keyboard import (
    get_mailing_selection_keyboard,
    get_test_mailing_keyboard,
)

router = Router()


class DebugStates(StatesGroup):
    select_mailing_for_test = State()


async def send_test_mailing(
    mailing: Mailing,
    bot: Bot,
    userbots: dict,
):
    """Отправляет тестовую рассылку немедленно."""
    logging.info(f"Начало ТЕСТОВОЙ рассылки: {mailing.name} (ID: {mailing.id})")

    target_chats = mailing.chat_ids
    userbot_name = mailing.userbot_name
    userbot = userbots.get(userbot_name)

    if not userbot or not userbot.client or not userbot.client.is_connected:
        error_msg = f"Юзербот {userbot_name} не найден или не активен для тестовой рассылки."
        logging.error(error_msg)
        for admin_id in admin_ids:
            await bot.send_message(admin_id, f"❌ Тестовая рассылка '{mailing.name}' не удалась. {error_msg}")
        return

    sent_count = 0
    failed_count = 0

    # Формируем контент рассылки как в продовой отправке: текст как подпись к медиагруппе
    package_path = os.path.join("msg", mailing.name)
    text = ""
    media_group: list[InputMediaPhoto | InputMediaVideo] = []

    if os.path.isdir(package_path):
        files = sorted(os.listdir(package_path))
        # Находим текст
        text_files = [f for f in files if f.lower().endswith(".txt")]
        if text_files:
            try:
                with open(os.path.join(package_path, text_files[0]), "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception as e:
                logging.error(f"Не удалось прочесть текст для тестовой рассылки '{mailing.name}': {e}")

        # Собираем фото/видео
        for f in files:
            lower = f.lower()
            full_path = os.path.join(package_path, f)
            if lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
                media_group.append(InputMediaPhoto(full_path))
            elif lower.endswith((".mp4", ".mov", ".mkv", ".webm")):
                media_group.append(InputMediaVideo(full_path))

        # Добавляем подпись только к первому элементу медиагруппы
        if media_group and text:
            first = media_group[0]
            if isinstance(first, InputMediaPhoto):
                media_group[0] = InputMediaPhoto(first.media, caption=text)
            elif isinstance(first, InputMediaVideo):
                media_group[0] = InputMediaVideo(first.media, caption=text)

    for chat in target_chats:
        # Готовим кандидаты ID: исходный, а для отрицательных чисел — с префиксом -100 как альтернатива
        candidates: list[object] = []
        try:
            as_int = int(chat)
            candidates.append(as_int)
            if as_int < -1000 and not str(as_int).startswith("-100"):
                candidates.append(int("-100" + str(abs(as_int))))
        except Exception:
            candidates.append(chat)

        delivered = False
        last_error: Exception | None = None
        for candidate in candidates:
            try:
                # Резолвим пира, чтобы избежать Peer id invalid
                try:
                    await userbot.client.resolve_peer(candidate)
                except Exception:
                    # Пытаемся получить чат (иногда помогает для каналов/супергрупп)
                    await userbot.client.get_chat(candidate)

                if media_group:
                    await userbot.client.send_media_group(candidate, media_group)
                elif text:
                    await userbot.client.send_message(candidate, text)
                else:
                    # Фоллбек: простое тестовое сообщение, если нет файлов и текста
                    await userbot.client.send_message(
                        candidate, f"🧪 Тестовое сообщение от рассылки '{mailing.name}'"
                    )
                sent_count += 1
                logging.info(f"Сообщение (тест) отправлено в чат {candidate} от {userbot_name}")
                delivered = True
                break
            except Exception as e:
                last_error = e

        if not delivered:
            failed_count += 1
            logging.error(f"Ошибка при тестовой отправке в чат {chat}: {last_error}")

    logging.info(f"Тестовая рассылка '{mailing.name}' завершена.")

    admin_message = (
        f"✅ Тестовая рассылка '{mailing.name}' завершена.\n\n"
        f"Отправлено: {sent_count}\n"
        f"Ошибок: {failed_count}"
    )
    for admin_id in admin_ids:
        await bot.send_message(admin_id, admin_message)


@router.message(Command("debug_mail"))
async def debug_start(message: Message):
    if message.from_user.id not in admin_ids:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return
    await message.answer(
        "Панель отладки. Нажмите кнопку для тестовой рассылки.",
        reply_markup=get_test_mailing_keyboard(),
    )


@router.callback_query(F.data == "test_mailing")
async def select_mailing_for_test(callback: CallbackQuery, state: FSMContext):
    mailings = mailing_service.get_all_mailings()
    if not mailings:
        await callback.message.edit_text("Нет созданных рассылок для теста.")
        await callback.answer()
        return

    await callback.message.edit_text(
        "Выберите рассылку для тестовой отправки:",
        reply_markup=get_mailing_selection_keyboard(mailings),
    )
    await state.set_state(DebugStates.select_mailing_for_test)
    await callback.answer()


@router.callback_query(DebugStates.select_mailing_for_test, F.data.startswith("mailing_"))
async def process_test_mailing(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    userbots: dict,
):
    # Сначала мгновенно отвечаем на callback, чтобы избежать таймаута Telegram
    try:
        await callback.answer("Тестовая рассылка инициирована.")
    except Exception:
        pass

    await callback.message.edit_text("Начинаю тестовую рассылку...")
    mailing_id = int(callback.data.split("_")[1])
    mailing = mailing_service.get_mailing(mailing_id)

    if not userbots:
        await callback.message.edit_text("Ошибка: Юзерботы не инициализированы.")
        await state.clear()
        return

    if not mailing:
        await callback.message.edit_text("Ошибка: Рассылка не найдена.")
        await state.clear()
        return

    # Запускаем отправку в фоне, чтобы не блокировать обработчик
    asyncio.create_task(send_test_mailing(mailing, bot, userbots))
    await state.clear()