from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import random
import logging

from keyboards.keyboards import (
    get_faq_apply_keyboard,
    get_reviews_navigation_keyboard,
    get_share_referral_keyboard,
    get_main_menu_new_user
)
from utils import messages
from database import db_manager, Application, Referral

router = Router()
logger = logging.getLogger(__name__)

# Список отзывов
REVIEWS = [
    '⭐⭐⭐⭐⭐\n"За 2 месяца я научился зарабатывать 800€ в месяц на криптовалюте. Отличный курс!" - Андрей, Германия',
    '⭐⭐⭐⭐⭐\n"Наконец-то понятное объяснение сложных вещей. Уже окупила время на обучение!" - Мария, Испания',
    '⭐⭐⭐⭐⭐\n"Личный наставник - это огромный плюс. Всегда помогал и отвечал на вопросы" - Дмитрий, Италия',
    '⭐⭐⭐⭐⭐\n"Начал с нуля, теперь управляю портфелем в 5000€. Спасибо за знания!" - Сергей, Франция',
    '⭐⭐⭐⭐⭐\n"Курс изменил мою жизнь! Уволилась с нелюбимой работы через 4 месяца" - Елена, Нидерланды',
    '⭐⭐⭐⭐⭐\n"Очень структурированная подача материала. Всё по полочкам!" - Виктор, Бельгия',
    '⭐⭐⭐⭐⭐\n"Реальные стратегии, которые работают. Зарабатываю 1200€/месяц" - Ольга, Австрия',
    '⭐⭐⭐⭐⭐\n"Лучшее вложение времени! Окупил обучение за первый месяц" - Павел, Швеция',
    '⭐⭐⭐⭐⭐\n"Преподаватели - настоящие профи. Объясняют так, что поймет каждый" - Анна, Польша',
    '⭐⭐⭐⭐⭐\n"Благодаря курсу создал пассивный доход 600€ в месяц" - Игорь, Чехия',
    '⭐⭐⭐⭐⭐\n"Супер поддержка! На все вопросы отвечают быстро и подробно" - Наталья, Португалия',
    '⭐⭐⭐⭐⭐\n"Теперь криптовалюта - мой основной источник дохода" - Александр, Греция',
    '⭐⭐⭐⭐⭐\n"Жалею только об одном - что не начал раньше!" - Михаил, Дания',
    '⭐⭐⭐⭐⭐\n"От страха перед криптой до уверенного трейдера за 2 месяца" - Татьяна, Финляндия',
    '⭐⭐⭐⭐⭐\n"Курс стоит каждой минуты! Рекомендую всем друзьям" - Владимир, Люксембург',
]

@router.callback_query(F.data == "program")
@router.message(Command("program"))
async def show_program(update: Message | CallbackQuery):
    """Показать программу курса"""
    if isinstance(update, CallbackQuery):
        await update.message.answer(messages.PROGRAM)
        await update.answer()
    else:
        await update.answer(messages.PROGRAM)

@router.callback_query(F.data == "faq")
async def show_faq(callback: CallbackQuery):
    """Показать FAQ"""
    await callback.message.answer(
        messages.FAQ,
        reply_markup=get_faq_apply_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "why_crypto")
async def show_why_crypto(callback: CallbackQuery):
    """Почему стоит изучать криптовалюты"""
    text = """💎 Почему стоит изучать криптовалюты:

📈 Растущий рынок - капитализация более $2 трлн
🌍 Глобальные возможности - работа из любой точки мира
💰 Высокий доход - от 500€ в месяц для начинающих
🔮 Технология будущего - блокчейн меняет мир
🛡️ Финансовая независимость - ваши деньги под вашим контролем
🚀 Раннее преимущество - мы еще в начале пути

Не упустите возможность стать частью финансовой революции!"""
    
    await callback.message.answer(text)
    await callback.answer()

@router.callback_query(F.data == "success_stories")
async def show_success_stories(callback: CallbackQuery):
    """Истории успеха"""
    text = """⭐ Истории успеха наших учеников:

🚀 **Александр (Польша)**: От 0 до 1500€/месяц за 3 месяца
"Начал без знаний, сейчас консультирую друзей по крипте"

🚀 **Елена (Чехия)**: Создала портфель на 10000€ с 500€
"Правильная стратегия - это всё. Спасибо наставнику!"

🚀 **Игорь (Германия)**: Уволился с работы через полгода
"Теперь занимаюсь только криптой и путешествую"

🚀 **Ольга (Франция)**: Запустила свой крипто-блог
"Курс дал не только знания, но и уверенность в себе"

🚀 **Михаил (Испания)**: От скептика до энтузиаста
"Думал это сложно, оказалось - проще чем кажется"

Следующая история успеха - ваша! 💪"""
    
    await callback.message.answer(text)
    await callback.answer()

@router.callback_query(F.data == "reviews")
@router.message(Command("reviews"))
async def show_reviews(update: Message | CallbackQuery, page: int = 1):
    """Показать отзывы"""
    reviews_per_page = 3
    total_pages = len(REVIEWS) // reviews_per_page
    
    start_idx = (page - 1) * reviews_per_page
    end_idx = start_idx + reviews_per_page
    
    current_reviews = REVIEWS[start_idx:end_idx]
    
    text = "💬 Отзывы наших выпускников:\n\n" + "\n\n".join(current_reviews)
    
    if isinstance(update, CallbackQuery):
        await update.message.answer(
            text,
            reply_markup=get_reviews_navigation_keyboard(page, total_pages)
        )
        await update.answer()
    else:
        await update.answer(
            text,
            reply_markup=get_reviews_navigation_keyboard(page, total_pages)
        )

@router.callback_query(F.data.startswith("reviews_page_"))
async def navigate_reviews(callback: CallbackQuery):
    """Навигация по отзывам"""
    page = int(callback.data.split("_")[2])
    
    reviews_per_page = 3
    total_pages = len(REVIEWS) // reviews_per_page
    
    start_idx = (page - 1) * reviews_per_page
    end_idx = start_idx + reviews_per_page
    
    current_reviews = REVIEWS[start_idx:end_idx]
    
    text = "💬 Отзывы наших выпускников:\n\n" + "\n\n".join(current_reviews)
    
    await callback.message.edit_text(
        text,
        reply_markup=get_reviews_navigation_keyboard(page, total_pages)
    )
    await callback.answer()

@router.callback_query(F.data == "referral")
async def show_referral_info(callback: CallbackQuery):
    """Информация о реферальной программе"""
    user_id = callback.from_user.id
    
    async with db_manager.get_session() as session:
        application = await session.query(Application).filter_by(user_id=user_id).first()
        
        if not application:
            await callback.message.answer(
                "❌ Реферальная программа доступна только после подачи заявки на курс!",
                reply_markup=get_main_menu_new_user()
            )
            await callback.answer()
            return
        
        # Считаем статистику
        referrals = await session.query(Referral).filter_by(referrer_id=user_id).all()
        referrals_count = len(referrals)
        
        # TODO: В будущем здесь будет подсчет завершивших 50% курса
        completed_count = 0
        earned = completed_count * 50
        pending = (referrals_count - completed_count) * 50
    
    bot_username = (await callback.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref{user_id}"
    
    text = f"""💰 Заработайте 50€ за каждого друга!

Как это работает:
1️⃣ Поделитесь вашей персональной ссылкой
2️⃣ Друг регистрируется на курс по вашей ссылке
3️⃣ Когда друг пройдет 50% курса, вы оба получите по 50€

Ваша ссылка:
{referral_link}

📊 Ваша статистика:
Приглашено друзей: {referrals_count}
Заработано: {earned}€

Поделитесь ссылкой прямо сейчас! 📲"""
    
    await callback.message.answer(
        text,
        reply_markup=get_share_referral_keyboard(referral_link)
    )
    await callback.answer()

@router.callback_query(F.data == "my_referrals")
async def show_my_referrals(callback: CallbackQuery):
    """Показать статистику рефералов"""
    user_id = callback.from_user.id
    
    async with db_manager.get_session() as session:
        # Считаем статистику
        referrals = await session.query(Referral).filter_by(referrer_id=user_id).all()
        referrals_count = len(referrals)
        
        # TODO: В будущем здесь будет подсчет завершивших 50% курса
        completed_count = 0
        earned = completed_count * 50
        pending = (referrals_count - completed_count) * 50
    
    bot_username = (await callback.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref{user_id}"
    
    text = f"""📊 Ваша реферальная статистика

👥 Приглашено друзей: {referrals_count}
✅ Завершили 50% курса: {completed_count}
💰 Заработано: {earned}€
⏳ Ожидается: {pending}€

Ваша реферальная ссылка:
{referral_link}

📤 Поделиться ссылкой"""
    
    await callback.message.answer(
        text,
        reply_markup=get_share_referral_keyboard(referral_link)
    )
    await callback.answer()

@router.callback_query(F.data == "copy_referral")
async def copy_referral_hint(callback: CallbackQuery):
    """Подсказка о копировании реферальной ссылки"""
    await callback.answer(
        "📋 Нажмите на ссылку и удерживайте для копирования",
        show_alert=True
    )

@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery):
    """Обработчик для кнопок без действия"""
    await callback.answer()

@router.message(Command("ref"))
async def cmd_referral(message: Message):
    """Быстрая команда для реферальной ссылки"""
    user_id = message.from_user.id
    
    async with db_manager.get_session() as session:
        application = await session.query(Application).filter_by(user_id=user_id).first()
        
        if not application:
            await message.answer(
                "❌ Реферальная программа доступна только после подачи заявки на курс!"
            )
            return
    
    bot_username = (await message.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref{user_id}"
    
    await message.answer(
        f"💰 Ваша реферальная ссылка:\n{referral_link}\n\n"
        f"Поделитесь с друзьями и получите по 50€!",
        reply_markup=get_share_referral_keyboard(referral_link)
    )
