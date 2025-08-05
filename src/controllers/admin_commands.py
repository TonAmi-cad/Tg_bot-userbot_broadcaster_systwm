from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.controllers.states import ReplyState
from src.core.userbot import UserBot
from typing import Dict

router = Router()


def get_action_keyboard(account_name: str) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Действие 1", callback_data=f"action:1:{account_name}"))
    builder.add(InlineKeyboardButton(text="Действие 2", callback_data=f"action:2:{account_name}"))
    builder.add(InlineKeyboardButton(text="Действие 3", callback_data=f"action:3:{account_name}"))
    builder.adjust(1)
    return builder.as_markup()


@router.callback_query(F.data.startswith("select_account:"))
async def select_account_handler(callback: CallbackQuery):
    account_name = callback.data.split(":")[1]
    await callback.message.edit_text(
        f"Выбран аккаунт: {account_name}\n\nВыберите действие:",
        reply_markup=get_action_keyboard(account_name)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("action:"))
async def action_handler(callback: CallbackQuery):
    _, action_id, account_name = callback.data.split(":")
    await callback.message.answer(f"Выполнено действие {action_id} для аккаунта {account_name}")
    await callback.answer()


@router.callback_query(F.data.startswith("reply:"))
async def reply_button_handler(callback: CallbackQuery, state: FSMContext):
    _, userbot_name, user_id = callback.data.split(":")
    await state.update_data(userbot_name=userbot_name, user_id=int(user_id))
    await state.set_state(ReplyState.waiting_for_reply)
    await callback.message.answer("Введите сообщение для ответа:")
    await callback.answer()


@router.message(ReplyState.waiting_for_reply)
async def send_reply_handler(message: Message, state: FSMContext, userbots: Dict[str, UserBot]):
    data = await state.get_data()
    userbot_name = data['userbot_name']
    user_id = data['user_id']
    
    userbot = userbots.get(userbot_name)

    if userbot:
        await userbot.client.send_message(chat_id=user_id, text=message.text)
        await message.answer("Сообщение отправлено.")
    else:
        await message.answer(f"Юзербот {userbot_name} не найден.")
        
    await state.clear()
