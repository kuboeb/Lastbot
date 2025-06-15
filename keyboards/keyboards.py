from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from utils import messages

def get_main_menu_new_user():
    """Главное меню для новых пользователей"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text=messages.BTN_APPLY, callback_data="apply"),
        InlineKeyboardButton(text=messages.BTN_PROGRAM, callback_data="program")
    )
    builder.row(
        InlineKeyboardButton(text=messages.BTN_REVIEWS, callback_data="reviews"),
        InlineKeyboardButton(text=messages.BTN_FAQ, callback_data="faq")
    )
    builder.row(
        InlineKeyboardButton(text=messages.BTN_WHY_CRYPTO, callback_data="why_crypto"),
        InlineKeyboardButton(text=messages.BTN_SUCCESS_STORIES, callback_data="success_stories")
    )
    
    return builder.as_markup()

def get_main_menu_existing_user():
    """Главное меню для пользователей с заявкой"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text=messages.BTN_REFERRAL, callback_data="referral"),
        InlineKeyboardButton(text=messages.BTN_MY_REFERRALS, callback_data="my_referrals")
    )
    builder.row(
        InlineKeyboardButton(text=messages.BTN_PROGRAM, callback_data="program"),
        InlineKeyboardButton(text=messages.BTN_REVIEWS, callback_data="reviews")
    )
    builder.row(
        InlineKeyboardButton(text=messages.BTN_FAQ, callback_data="faq"),
        InlineKeyboardButton(text=messages.BTN_WHY_CRYPTO, callback_data="why_crypto")
    )
    builder.row(
        InlineKeyboardButton(text=messages.BTN_SUCCESS_STORIES, callback_data="success_stories")
    )
    
    return builder.as_markup()

def get_reply_keyboard_new_user():
    """Reply клавиатура для новых пользователей"""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text=messages.BTN_MAIN_MENU),
        KeyboardButton(text=messages.BTN_ABOUT)
    )
    
    return builder.as_markup(resize_keyboard=True)

def get_reply_keyboard_existing_user():
    """Reply клавиатура для пользователей с заявкой"""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text=messages.BTN_MAIN_MENU),
        KeyboardButton(text="💰 Реферальная ссылка")
    )
    
    return builder.as_markup(resize_keyboard=True)

def get_back_keyboard():
    """Клавиатура с кнопкой Назад"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=messages.BTN_BACK))
    return builder.as_markup(resize_keyboard=True)

def get_time_selection_keyboard():
    """Клавиатура выбора времени для звонка"""
    builder = InlineKeyboardBuilder()
    
    times = [
        ("📅 9:00 - 12:00", "time_9_12"),
        ("📅 12:00 - 15:00", "time_12_15"),
        ("📅 15:00 - 18:00", "time_15_18"),
        ("📅 18:00 - 21:00", "time_18_21")
    ]
    
    for text, callback in times:
        builder.add(InlineKeyboardButton(text=text, callback_data=callback))
    
    builder.adjust(2)
    return builder.as_markup()

def get_confirmation_keyboard():
    """Клавиатура подтверждения данных"""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text=messages.BTN_CONFIRM),
        KeyboardButton(text=messages.BTN_EDIT)
    )
    builder.row(
        KeyboardButton(text=messages.BTN_BACK)
    )
    
    return builder.as_markup(resize_keyboard=True)

def get_share_referral_keyboard(referral_link: str):
    """Клавиатура для шаринга реферальной ссылки"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📤 Переслать другу",
            switch_inline_query=f"Приглашаю тебя на бесплатный курс по криптовалюте! Мы оба получим по 50€ когда ты пройдешь половину курса 💰\n\n{referral_link}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📋 Скопировать ссылку",
            callback_data="copy_referral"
        )
    )
    
    return builder.as_markup()

def get_reviews_navigation_keyboard(current_page: int = 1, total_pages: int = 5):
    """Навигация по отзывам"""
    builder = InlineKeyboardBuilder()
    
    # Кнопки навигации
    buttons = []
    if current_page > 1:
        buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"reviews_page_{current_page-1}"))
    
    buttons.append(InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="noop"))
    
    if current_page < total_pages:
        buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"reviews_page_{current_page+1}"))
    
    builder.row(*buttons)
    
    # Кнопка записи на курс
    builder.row(InlineKeyboardButton(text="🚀 Хочу так же!", callback_data="apply"))
    
    return builder.as_markup()

def get_faq_apply_keyboard():
    """Кнопка записи после FAQ"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🚀 Хочу на курс!", callback_data="apply"))
    return builder.as_markup()
