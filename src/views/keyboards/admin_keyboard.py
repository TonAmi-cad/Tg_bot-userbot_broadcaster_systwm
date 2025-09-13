from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Создать рассылку", callback_data="create_mailing"),
    )
    builder.row(
        InlineKeyboardButton(text="Редактировать рассылку", callback_data="edit_mailing"),
    )
    builder.row(
        InlineKeyboardButton(text="Восстановить базу", callback_data="restore_database"),
    )
    return builder.as_markup()
