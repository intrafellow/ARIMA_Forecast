# keyboard.py
from aiogram.utils.keyboard import InlineKeyboardBuilder

main_menu = InlineKeyboardBuilder()
main_menu.button(text="Построить график!", callback_data="make_graphic")
main_menu = main_menu.as_markup()
