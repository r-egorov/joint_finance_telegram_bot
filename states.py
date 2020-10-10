from aiogram.utils.helper import Helper, HelperMode, ListItem
from aiogram.dispatcher.filters.state import State, StatesGroup


class UserState(StatesGroup):
    IDLE = State()
    MAIN_MENU = State()
    NOT_REGISTERED = State()
    CHOOSE_BUDGET = State()
    PERSONAL_BUDGET = State()
    JOINT_BUDGET = State()



