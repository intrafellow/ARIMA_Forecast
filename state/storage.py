
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

class Graphic(StatesGroup):
    file = State()
    column = State()
    graphics_to_build = State()
    period = State()
    restart = State()


storage = MemoryStorage()
