"""
Клавиатуры для бота
"""
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from utils import messages

# Reply клавиатуры

def get_reply_keyboard_new_user():
    """Reply клавиатура для новых пользователей"""
    keyboard = [
        [KeyboardButton(text="🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_reply_keyboard_existing_user():
    """Reply клавиатура для существующих пользователей"""
    keyboard = [
        [KeyboardButton(text="💰 Реферальная ссылка")],
        [KeyboardButton(text="🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_registration_keyboard():
    """Reply клавиатура для процесса регистрации"""
    keyboard = [
        [KeyboardButton(text=messages.BTN_BACK)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Inline клавиатуры

def get_main_menu_new_user():
    """Главное меню для новых пользователей"""
    keyboard = [
        [InlineKeyboardButton(text="✅ Записаться на курс", callback_data="apply")],
        [
            InlineKeyboardButton(text="📚 О курсе", callback_data="about_course"),
            InlineKeyboardButton(text="💬 Отзывы", callback_data="reviews")
        ],
        [
            InlineKeyboardButton(text="❓ FAQ", callback_data="faq"),
            InlineKeyboardButton(text="🎯 Программа", callback_data="program")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_main_menu_existing_user():
    """Главное меню для пользователей с заявкой"""
    keyboard = [
        [InlineKeyboardButton(text="💰 50€ за друга", callback_data="referral_info")],
        [InlineKeyboardButton(text="📊 Мои рефералы", callback_data="my_referrals")],
        [
            InlineKeyboardButton(text="📚 О курсе", callback_data="about_course"),
            InlineKeyboardButton(text="💬 Отзывы", callback_data="reviews")
        ],
        [
            InlineKeyboardButton(text="❓ FAQ", callback_data="faq"),
            InlineKeyboardButton(text="🎯 Программа", callback_data="program")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_back_button():
    """Кнопка назад"""
    keyboard = [
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_time_selection_keyboard():
    """Клавиатура выбора времени"""
    keyboard = [
        [
            InlineKeyboardButton(text="📅 9:00 - 12:00", callback_data="time_9_12"),
            InlineKeyboardButton(text="📅 12:00 - 15:00", callback_data="time_12_15")
        ],
        [
            InlineKeyboardButton(text="📅 15:00 - 18:00", callback_data="time_15_18"),
            InlineKeyboardButton(text="📅 18:00 - 21:00", callback_data="time_18_21")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_confirmation_keyboard():
    """Клавиатура подтверждения"""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm"),
            InlineKeyboardButton(text="✏️ Изменить", callback_data="edit")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
