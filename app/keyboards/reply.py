from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from app.lexicon.lexicon_ru import LEXICON

def main_menu_reply_keyboard() -> ReplyKeyboardMarkup:
    """Создает постоянную клавиатуру с кнопкой 'Меню'."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LEXICON['main_menu_button'])]
        ],
        resize_keyboard=True
    )