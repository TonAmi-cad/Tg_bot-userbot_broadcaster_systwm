from aiogram.fsm.state import StatesGroup, State


class CreateMailing(StatesGroup):
    waiting_for_package_name = State()
    waiting_for_userbot = State()
    waiting_for_chats = State()
    waiting_for_mailing_message = State()
    waiting_for_period_unit = State()
    waiting_for_period_value = State()
    confirm = State()

class EditMailing(StatesGroup):
    choosing_mailing_to_edit = State()
    editing_menu = State()
    editing_package = State()
    editing_text = State()
    adding_photos = State()
    deleting_photos = State()
    editing_period = State()

class States(StatesGroup):
    waiting_for_name = State()
    waiting_for_price_buy = State()
    waiting_for_price_sell = State()
    editing_motivational_post = State()
    confirming_motivational_post = State()
    hiding_posts = State()
    deleting_posts = State()
    adding_posts = State()
    waiting_for_post_time = State()
    waiting_for_motivational_post_time = State()
    viewing_post = State()
