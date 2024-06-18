from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from functions import functions as func
from keyboards import keyboard as kb
from state.storage import Graphic

router = Router()

@router.callback_query()
async def callback_handler(call: types.CallbackQuery, state: FSMContext):
    user_id = int(call.from_user.id)

    if call.data == "make_graphic":
        await call.answer()

        await state.set_state(Graphic.file)
        await call.message.answer("Загрузите файл в формате .csv, по которому будет строиться график")
