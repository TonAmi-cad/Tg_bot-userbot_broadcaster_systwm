from aiogram.fsm.state import StatesGroup, State


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

