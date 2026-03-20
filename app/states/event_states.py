from aiogram.fsm.state import State, StatesGroup


class AddEventFSM(StatesGroup):
    """Состояния для добавления события"""
    waiting_for_title = State()
    waiting_for_date = State()
    waiting_for_type = State()
    waiting_for_remind_days = State()


class DeleteEventFSM(StatesGroup):
    """Состояния для удаления события"""
    waiting_for_event_id = State()
