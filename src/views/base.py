from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Any


class BaseButton:

    @staticmethod
    def create_buttons(data: List[Any], callback_data: List[Any], include_back=False, back_callback: str = None):
        builder = InlineKeyboardBuilder()

        for i, j in zip(data, callback_data):
            builder.row(InlineKeyboardButton(text=i, callback_data=j))
        if include_back:
            builder.row(InlineKeyboardButton(text=" 🔙 Назад", callback_data=back_callback))

        return builder
