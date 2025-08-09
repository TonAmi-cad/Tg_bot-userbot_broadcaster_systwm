import re
import os
from datetime import timedelta, datetime
from typing import Dict, List

from aiogram import F, Bot, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery, InputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.core.dependencies import config
from src.core.states import CreateMailing, EditMailing
from src.core.userbot import UserBot
from src.views.services import MailingService
from src.core.scheduler import send_mailing, schedule_mailing_for


admin_router = Router()


def get_userbot_keyboard():
    builder = InlineKeyboardBuilder()
    for account in config.userbot_account.userbot_account:
        builder.add(InlineKeyboardButton(text=account['name'], callback_data=f"userbot:{account['name']}"))
    builder.adjust(1)
    return builder.as_markup()


@admin_router.message(Command("start"))
async def start_handler(message: Message, admin_ids: List[int]):
    if message.from_user.id in admin_ids:
        await message.answer("Добро пожаловать, администратор!")
    else:
        await message.answer("У вас нет прав доступа.")


@admin_router.message(Command("create_mailing"))
async def create_mailing_start(message: Message, state: FSMContext, admin_ids: List[int]):
    if message.from_user.id not in admin_ids:
        await message.answer("У вас нет прав доступа.")
        return
    await message.answer("Введите название пакета рассылки (это будет имя папки в `msg/`):")
    await state.set_state(CreateMailing.waiting_for_package_name)


@admin_router.message(CreateMailing.waiting_for_package_name)
async def process_package_name(message: Message, state: FSMContext):
    await state.update_data(package_name=message.text)
    os.makedirs(os.path.join("msg", message.text), exist_ok=True)
    await message.answer("Выберите юзербота для рассылки:", reply_markup=get_userbot_keyboard())
    await state.set_state(CreateMailing.waiting_for_userbot)


@admin_router.callback_query(F.data.startswith("userbot:"))
async def process_userbot_selection(callback_query: CallbackQuery, state: FSMContext):
    userbot_name = callback_query.data.split(":")[1]
    await state.update_data(userbot_name=userbot_name)
    await callback_query.message.answer("Введите ID чатов для рассылки через запятую:")
    await state.set_state(CreateMailing.waiting_for_chats)


@admin_router.message(CreateMailing.waiting_for_chats)
async def process_chat_ids(message: Message, state: FSMContext):
    try:
        chat_ids = [int(chat_id.strip()) for chat_id in message.text.split(',')]
        await state.update_data(chat_ids=chat_ids)
        await message.answer(
            "Теперь отправьте сообщение, которое будет использоваться в рассылке. "
            "Вы можете прикрепить фото и добавить к ним текст. "
            "Обратите внимание: бот обработает только одно сообщение (текст или фото с подписью)."
        )
        await state.set_state(CreateMailing.waiting_for_mailing_message)
    except ValueError:
        await message.answer("Неверный формат ID чатов. Пожалуйста, введите ID через запятую (например: -100123456789, -100987654321).")


@admin_router.message(CreateMailing.waiting_for_mailing_message, F.text | F.photo)
async def process_mailing_message(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    package_path = os.path.join("msg", data['package_name'])

    text = message.text or message.caption
    if text:
        with open(os.path.join(package_path, "text.txt"), "w", encoding="utf-8") as f:
            f.write(text)

    if message.photo:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file_name = f"{photo.file_unique_id}.jpg"
        await bot.download_file(file_info.file_path, os.path.join(package_path, file_name))

    await message.answer("Сообщение для рассылки сохранено.")

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Дни", callback_data="period_unit:days"))
    builder.add(InlineKeyboardButton(text="Часы", callback_data="period_unit:hours"))
    await message.answer("Выберите единицу измерения для периода рассылки:", reply_markup=builder.as_markup())
    await state.set_state(CreateMailing.waiting_for_period_unit)


@admin_router.callback_query(F.data.startswith("period_unit:"))
async def process_period_unit(callback_query: CallbackQuery, state: FSMContext):
    unit = callback_query.data.split(":")[1]
    await state.update_data(period_unit=unit)
    if unit == "days":
        await callback_query.message.answer("Введите период рассылки в днях:")
    else:
        await callback_query.message.answer("Введите период рассылки в часах:")
    await state.set_state(CreateMailing.waiting_for_period_value)


@admin_router.message(CreateMailing.waiting_for_period_value)
async def process_period_value(message: Message, state: FSMContext, mailing_service: MailingService, scheduler: AsyncIOScheduler):
    try:
        period_value = int(message.text)
        data = await state.get_data()
        period_unit = data.get("period_unit", "hours") 

        if period_unit == "days":
            period = timedelta(days=period_value)
        else:
            period = timedelta(hours=period_value)

        mailing_info = {
            "name": data['package_name'],
            "userbot_name": data['userbot_name'],
            "chat_ids": data['chat_ids'],
            "period": period,
        }
        mailing = mailing_service.create_mailing(mailing_info)

        # Немедленный первый запуск и корректный интервал через единую функцию
        schedule_mailing_for(mailing, scheduler, datetime.utcnow())

        await message.answer(f"Рассылка '{data['package_name']}' успешно создана и первый запуск выполнится сразу!")
        await state.clear()
    except ValueError:
        await message.answer("Неверный формат периода. Пожалуйста, введите целое число.")
    except Exception as e:
        await message.answer(f"Произошла ошибка при создании рассылки: {e}")
        await state.clear()


@admin_router.message(Command("edit_mailing"))
async def edit_mailing_start(message: Message, mailing_service: MailingService, admin_ids: List[int]):
    if message.from_user.id not in admin_ids:
        await message.answer("У вас нет прав доступа.")
        return
        
    mailings = mailing_service.get_all_mailings()
    if not mailings:
        await message.answer("Нет созданных рассылок для редактирования.")
        return

    builder = InlineKeyboardBuilder()
    for mailing in mailings:
        builder.add(InlineKeyboardButton(text=mailing.name, callback_data=f"edit_mailing:{mailing.id}"))
    builder.adjust(1)
    await message.answer("Выберите рассылку для редактирования:", reply_markup=builder.as_markup())


@admin_router.callback_query(F.data.startswith("edit_mailing:"))
async def process_mailing_selection_for_edit(callback_query: CallbackQuery, state: FSMContext):
    mailing_id = int(callback_query.data.split(":")[1])
    await state.update_data(mailing_id=mailing_id)

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Изменить текст", callback_data="edit_text"))
    builder.add(InlineKeyboardButton(text="Добавить фото", callback_data="add_photos"))
    builder.add(InlineKeyboardButton(text="Удалить фото", callback_data="delete_photos"))
    builder.add(InlineKeyboardButton(text="Изменить период", callback_data="edit_period"))
    builder.adjust(1)

    await callback_query.message.edit_text("Что вы хотите изменить?", reply_markup=builder.as_markup())
    await state.set_state(EditMailing.editing_menu)


@admin_router.callback_query(F.data == "edit_text", EditMailing.editing_menu)
async def process_edit_text_start(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Пришлите новый текст для рассылки.")
    await state.set_state(EditMailing.editing_text)


@admin_router.message(EditMailing.editing_text)
async def process_edit_text_finish(message: Message, state: FSMContext, mailing_service: MailingService):
    try:
        data = await state.get_data()
        mailing_id = data['mailing_id']
        mailing = mailing_service.get_mailing(mailing_id)
        
        package_path = os.path.join("msg", mailing.name)
        text_files = [f for f in os.listdir(package_path) if f.lower().endswith('.txt')]

        if not text_files:
            with open(os.path.join(package_path, "text.txt"), "w", encoding="utf-8") as f:
                f.write(message.text)
        else:
            with open(os.path.join(package_path, text_files[0]), "w", encoding="utf-8") as f:
                f.write(message.text)

        await message.answer("Текст рассылки успешно обновлен!")
        await state.clear()

    except Exception as e:
        await message.answer(f"Произошла ошибка при обновлении текста: {e}")
        await state.clear()


@admin_router.callback_query(F.data == "add_photos", EditMailing.editing_menu)
async def process_add_photos_start(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Пришлите фотографии для добавления в рассылку. Когда закончите, нажмите /done.")
    await state.set_state(EditMailing.adding_photos)


@admin_router.message(F.photo, EditMailing.adding_photos)
async def process_add_photos_finish(message: Message, state: FSMContext, mailing_service: MailingService, bot: Bot):
    try:
        data = await state.get_data()
        mailing_id = data['mailing_id']
        mailing = mailing_service.get_mailing(mailing_id)
        
        package_path = os.path.join("msg", mailing.name)
        
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file_path = file_info.file_path
        
        file_name = f"{photo.file_unique_id}.jpg"
        
        await bot.download_file(file_path, os.path.join(package_path, file_name))
        await message.answer("Фото добавлено.")

    except Exception as e:
        await message.answer(f"Произошла ошибка при добавлении фото: {e}")


@admin_router.message(Command("done"), EditMailing.adding_photos)
async def process_add_photos_done(message: Message, state: FSMContext):
    await message.answer("Добавление фотографий завершено.")
    await state.clear()


@admin_router.callback_query(F.data == "delete_photos", EditMailing.editing_menu)
async def process_delete_photos_start(callback_query: CallbackQuery, state: FSMContext, mailing_service: MailingService):
    data = await state.get_data()
    mailing_id = data['mailing_id']
    mailing = mailing_service.get_mailing(mailing_id)
    
    package_path = os.path.join("msg", mailing.name)
    photos = [f for f in os.listdir(package_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if not photos:
        await callback_query.message.answer("В этой рассылке нет фотографий для удаления.")
        await state.clear()
        return

    builder = InlineKeyboardBuilder()
    for photo in photos:
        builder.add(InlineKeyboardButton(text=photo, callback_data=f"delete_photo:{photo}"))
    builder.adjust(1)
    
    await callback_query.message.answer("Выберите фотографии для удаления:", reply_markup=builder.as_markup())
    await state.set_state(EditMailing.deleting_photos)


@admin_router.callback_query(F.data.startswith("delete_photo:"), EditMailing.deleting_photos)
async def process_delete_photo_finish(callback_query: CallbackQuery, state: FSMContext, mailing_service: MailingService):
    try:
        photo_name = callback_query.data.split(":")[1]
        data = await state.get_data()
        mailing_id = data['mailing_id']
        mailing = mailing_service.get_mailing(mailing_id)
        
        package_path = os.path.join("msg", mailing.name)
        os.remove(os.path.join(package_path, photo_name))

        await callback_query.message.edit_text(f"Фотография {photo_name} удалена.")
        await state.clear()
    except Exception as e:
        await callback_query.message.answer(f"Произошла ошибка при удалении фото: {e}")
        await state.clear()


@admin_router.callback_query(F.data == "edit_period", EditMailing.editing_menu)
async def process_edit_period_start(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите новый период рассылки в часах:")
    await state.set_state(EditMailing.editing_period)


@admin_router.message(EditMailing.editing_period)
async def process_edit_period_finish(message: Message, state: FSMContext, mailing_service: MailingService, scheduler: AsyncIOScheduler):
    try:
        period_hours = int(message.text)
        data = await state.get_data()
        mailing_id = data['mailing_id']

        mailing_service.update_mailing(mailing_id, {"period": timedelta(hours=period_hours)})

        scheduler.reschedule_job(f"mailing_{mailing_id}", trigger='interval', seconds=timedelta(hours=period_hours).total_seconds())

        await message.answer("Период рассылки успешно обновлен!")
        await state.clear()
    except ValueError:
        await message.answer("Неверный формат периода. Пожалуйста, введите количество часов (например: 24).")
    except Exception as e:
        await message.answer(f"Произошла ошибка при обновлении периода: {e}")
        await state.clear()


@admin_router.message(F.reply_to_message)
async def admin_reply_handler(message: Message, userbots: Dict[str, UserBot]):
    if message.reply_to_message.from_user.is_bot:
        reply_text = message.reply_to_message.text

        match = re.search(r"(\d+):(.+)", reply_text.split('\n')[-1])

        if match:
            user_id, userbot_name = match.groups()
            user_id = int(user_id)

            userbot = userbots.get(userbot_name)

            if userbot:
                try:
                    await userbot.client.send_message(chat_id=user_id, text=message.text)
                    await message.answer("✅ Сообщение отправлено.")
                except Exception as e:
                    await message.answer(f"❌ Не удалось отправить сообщение: {e}")
            else:
                await message.answer(f"❌ Юзербот с именем '{userbot_name}' не найден.")
        else:
            pass

