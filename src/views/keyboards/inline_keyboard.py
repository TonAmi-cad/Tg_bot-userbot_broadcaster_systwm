from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from src.models.models import Mailing
from typing import List

def get_test_mailing_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Тест рассылки", callback_data="test_mailing")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_mailing_selection_keyboard(mailings: List[Mailing]):
    buttons = []
    for mailing in mailings:
        buttons.append([InlineKeyboardButton(text=mailing.name, callback_data=f"mailing_{mailing.id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
