from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.views.base import BaseButton

def get_channel_links_button(channels):
    builder = InlineKeyboardBuilder()
    for channel in channels:
        builder.row(InlineKeyboardButton(text=channel["name"], url=channel["url"]))
    builder.row(InlineKeyboardButton(text="✅ Я людина", callback_data="check_subscription"))
    return builder.as_markup()


def go_to_channel_button(url: str):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🚘 ПЕРЕЙТИ В КАНАЛ", url=url))
    return builder.as_markup()
