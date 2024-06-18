# handlers.py
from aiogram.filters.command import Command
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram import Bot
from aiogram.types.input_file import FSInputFile

from keyboards import keyboard as kb
from functions import functions as func
from state.storage import Graphic
import logging

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    logging.info("Command /start received")
    await message.answer("Привет! 👋\nЧтобы построить график нажмите на кнопку ниже.\nДанные советую брать с сайта: https://finance.yahoo.com/",
                         reply_markup=kb.main_menu)


@router.message(Graphic.file)
async def get_file(message: types.Message, state: FSMContext, bot: Bot):
    if message.document is None:
        await message.answer("Вы не прикрепили файл",
                             reply_markup=kb.main_menu)
    else:
        # Проверка расширения файла
        if not message.document.file_name.endswith('.csv'):
            await message.answer("Упсссссс, Вы ошиблись с расширением файла. 🤭\nПрикрепите, пожалуйста, файл .csv",
                                 reply_markup=kb.main_menu)
            return

        file = await bot.get_file(file_id=message.document.file_id)
        await bot.download_file(file_path=file.file_path, destination=message.document.file_name)
        await state.update_data(file=message.document.file_name)

        await state.set_state(Graphic.column)
        await message.answer(text='Введите название колонки, по которой будет строиться график:')


@router.message(Graphic.column)
async def set_column(message: types.Message, state: FSMContext):
    column = message.text
    await state.update_data(column=column)

    await state.set_state(Graphic.graphics_to_build)
    await message.answer(text='Введите номера графиков через запятую (1, 2, 3, 4, 5, 6), которые необходимо построить:'
                              '\n1. График исторических данных'
                              '\n2. График прогноза на выбранный период'
                              '\n3. График ACF/PACF'
                              '\n4. График остатков'
                              '\n5. Загрузить новый файл'
                              '\n6. Завершение диалога')

@router.message(Graphic.graphics_to_build)
async def create_graphics(message: types.Message, state: FSMContext, bot: Bot):
    graphics_to_build = message.text.split(',')
    await state.update_data(graphics_to_build=graphics_to_build)
    state_data = await state.get_data()
    filename = state_data['file']
    column = state_data['column']

    if '6' in graphics_to_build:
        await message.answer(text='Диалог завершен.\nСпасибо за плодотворную работу!\nДля продолжения диалога введите любую цифру из тех, что предлагались ранее\nЖдем вас снова!👋')
        return

    if '5' in graphics_to_build:
        await state.set_state(Graphic.file)
        await message.answer(text='Загрузите файл в формате .csv, по которому будет строиться график.')
        return

    if '2' in graphics_to_build:
        await state.set_state(Graphic.period)
        await message.answer(text='Введите период прогнозирования в днях:')
    else:
        func.make_graphic(filename=filename, column=column, graphics_to_build=graphics_to_build)
        await send_graphics(message, graphics_to_build, bot)
        await state.set_state(Graphic.graphics_to_build)
        await message.answer(text='Введите номера графиков через запятую (1, 2, 3, 4, 5, 6), которые необходимо построить:'
                                  '\n1. График исторических данных'
                                  '\n2. График прогноза на выбранный период'
                                  '\n3. График ACF/PACF'
                                  '\n4. График остатков'
                                  '\n5. Загрузить новый файл'
                                  '\n6. Завершение диалога')

@router.message(Graphic.period)
async def set_period(message: types.Message, state: FSMContext, bot: Bot):
    period = int(message.text)
    state_data = await state.get_data()
    filename = state_data['file']
    column = state_data['column']
    graphics_to_build = state_data['graphics_to_build']

    func.make_graphic(filename=filename, column=column, graphics_to_build=graphics_to_build, period=period)
    await send_graphics(message, graphics_to_build, bot, period)

    await state.set_state(Graphic.graphics_to_build)
    await message.answer(text='Введите номера графиков через запятую (1, 2, 3, 4, 5, 6), которые необходимо построить:'
                              '\n1. График исторических данных'
                              '\n2. График прогноза на выбранный период'
                              '\n3. График ACF/PACF'
                              '\n4. График остатков'
                              '\n5. Загрузить новый файл'
                              '\n6. Завершение диалога')

async def send_graphics(message: types.Message, graphics_to_build: list, bot: Bot, period: int = None):
    if '1' in graphics_to_build:
        await message.answer_photo(photo=FSInputFile('time_series_plot.png'),
                                   caption="График временного ряда")
    if '2' in graphics_to_build and period is not None:
        await message.answer_photo(photo=FSInputFile('forecast_plot.png'),
                                   caption=f"График прогноза на {period} дней")
    if '3' in graphics_to_build:
        await message.answer_photo(photo=FSInputFile('acf_pacf_plot.png'),
                                   caption="График ACF и PACF")
    if '4' in graphics_to_build:
        await message.answer_photo(photo=FSInputFile('residuals_plot.png'),
                                   caption="График остатков")

@router.message(Graphic.restart)
async def restart_process(message: types.Message, state: FSMContext):
    if message.text == '5':
        await state.set_state(Graphic.file)
        await message.answer(text='Загрузите файл в формате .csv, по которому будет строиться график.')
    else:
        await cmd_start(message)
