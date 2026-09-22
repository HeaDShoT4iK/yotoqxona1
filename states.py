from aiogram.fsm.state import State, StatesGroup


class CommentStates(StatesGroup):
    """Guruhdagi admin ticket statusi uchun izoh yozayotganda ishlatiladi."""
    waiting_comment = State()


class StaffStates(StatesGroup):
    waiting_new_admin = State()
    waiting_remove_admin = State()


class BroadcastStates(StatesGroup):
    waiting_text = State()
    waiting_confirm = State()


class BlockStates(StatesGroup):
    waiting_block_code = State()
    waiting_unblock_code = State()
