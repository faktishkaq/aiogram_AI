from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_HELP = "ℹ️ Помощь"
BTN_NEW = "🔄 Новый диалог"

MENU_BUTTONS = {BTN_HELP, BTN_NEW}


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_HELP), KeyboardButton(text=BTN_NEW)],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Напишите сообщение, отправьте фото или голосовое...",
    )
