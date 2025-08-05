from aiogram.fsm.state import State, StatesGroup

class ReplyState(StatesGroup):
    waiting_for_reply = State()
