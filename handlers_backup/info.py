"""
Обработчики информационных команд
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func
import random

from database import db_manager, Application, Referral, BotUser
from keyboards.keyboards import get_back_button
from utils import messages

router = Router(name="info")

# Список отзывов для случайного выбора
REVIEWS = [
    "⭐⭐⭐⭐⭐\n\"За 2 месяца я научился зарабатывать 800€ в месяц на криптовалюте. Отличный курс!\" - Андрей, Германия",
    "⭐⭐⭐⭐⭐\n\"Наконец-то понятное объяснение сложных вещей. Уже окупила время на обучение!\" - Мария, Испания",
    "⭐⭐⭐⭐⭐\n\"Личный наставник - это огромный плюс. Всегда помогал и отвечал на вопросы\" - Дмитрий, Италия",
    "⭐⭐⭐⭐⭐\n\"Начал с нуля, теперь управляю портфелем в 5000€. Спасибо за знания!\" - Сергей, Франция",
    "⭐⭐⭐⭐⭐\n\"Курс изменил мою жизнь! Уволилась с нелюбимой работы через 4 месяца\" - Елена, Нидерланды",
    "⭐⭐⭐⭐⭐\n\"Очень структурированная подача материала. Всё по полочкам!\" - Виктор, Бельгия",
    "⭐⭐⭐⭐⭐\n\"Реальные стратегии, которые работают. Зарабатываю 1200€/месяц\" - Ольга, Австрия",
    "⭐⭐⭐⭐⭐\n\"Лучшее вложение времени! Окупил обучение за первый месяц\" - Павел, Швеция",
    "⭐⭐⭐⭐⭐\n\"Преподаватели - настоящие профи. Объясняют так, что поймет каждый\" - Анна, Польша",
    "⭐⭐⭐⭐⭐\n\"Благодаря курсу создал пассивный доход 600€ в месяц\" - Игорь, Чехия",
    "⭐⭐⭐⭐⭐\n\"Супер поддержка! На все вопросы отвечают быстро и подробно\" - Наталья, Португалия",
    "⭐⭐⭐⭐⭐\n\"Теперь криптовалюта - мой основной источник дохода\" - Александр, Греция",
    "⭐⭐⭐⭐⭐\n\"Жалею только об одном - что не начал раньше!\" - Михаил, Дания",
    "⭐⭐⭐⭐⭐\n\"От страха перед криптой до уверенного трейдера за 2 месяца\" - Татьяна, Финляндия",
    "⭐⭐⭐⭐⭐\n\"Курс стоит каждой минуты! Рекомендую всем друзьям\" - Владимир, Люксембург"
]

@router.callback_query(F.data == "program")
async def show_program(callback: CallbackQuery):
    """Показать программу курса"""
    await callback.message.edit_text(
        messages.COURSE_PROGRAM,
        reply_markup=get_back_button()
    )
    await callback.answer()

@router.message(F.text == messages.BTN_PROGRAM)
async def show_program_msg(message: Message):
    """Показать программу курса через кнопку"""
    await message.answer(
        messages.COURSE_PROGRAM,
        reply_markup=get_back_button()
    )

async def show_program(message: Message):
    """Функция для показа программы (для команды)"""
    await message.answer(
        messages.COURSE_PROGRAM,
        reply_markup=get_back_button()
    )

@router.callback_query(F.data == "reviews")
async def show_reviews_callback(callback: CallbackQuery):
    """Показать отзывы"""
    # Выбираем 4 случайных отзыва
    selected_reviews = random.sample(REVIEWS, 4)
    reviews_text = "💬 Отзывы наших выпускников:\n\n" + "\n\n".join(selected_reviews)
    
    await callback.message.edit_text(
        reviews_text,
        reply_markup=get_back_button()
    )
    await callback.answer()

@router.message(F.text == messages.BTN_REVIEWS)
async def show_reviews_msg(message: Message):
    """Показать отзывы через кнопку"""
    selected_reviews = random.sample(REVIEWS, 4)
    reviews_text = "💬 Отзывы наших выпускников:\n\n" + "\n\n".join(selected_reviews)
    
    await message.answer(
        reviews_text,
        reply_markup=get_back_button()
    )

async def show_reviews(message: Message):
    """Функция для показа отзывов (для команды)"""
    selected_reviews = random.sample(REVIEWS, 4)
    reviews_text = "💬 Отзывы наших выпускников:\n\n" + "\n\n".join(selected_reviews)
    
    await message.answer(
        reviews_text,
        reply_markup=get_back_button()
    )

@router.callback_query(F.data == "faq")
async def show_faq(callback: CallbackQuery):
    """Показать FAQ"""
    await callback.message.edit_text(
        messages.FAQ_TEXT,
        reply_markup=get_back_button()
    )
    await callback.answer()

@router.message(F.text == messages.BTN_FAQ)
async def show_faq_msg(message: Message):
    """Показать FAQ через кнопку"""
    await message.answer(
        messages.FAQ_TEXT,
        reply_markup=get_back_button()
    )

@router.callback_query(F.data == "why_crypto")
async def show_why_crypto(callback: CallbackQuery):
    """Почему крипто"""
    await callback.message.edit_text(
        messages.WHY_CRYPTO,
        reply_markup=get_back_button()
    )
    await callback.answer()

@router.message(F.text == messages.BTN_WHY_CRYPTO)
async def show_why_crypto_msg(message: Message):
    """Почему крипто через кнопку"""
    await message.answer(
        messages.WHY_CRYPTO,
        reply_markup=get_back_button()
    )

@router.callback_query(F.data == "success_stories")
async def show_success_stories(callback: CallbackQuery):
    """Истории успеха"""
    await callback.message.edit_text(
        messages.SUCCESS_STORIES,
        reply_markup=get_back_button()
    )
    await callback.answer()

@router.message(F.text == messages.BTN_SUCCESS_STORIES)
async def show_success_stories_msg(message: Message):
    """Истории успеха через кнопку"""
    await message.answer(
        messages.SUCCESS_STORIES,
        reply_markup=get_back_button()
    )

@router.callback_query(F.data == "about_course")
async def show_about_course(callback: CallbackQuery):
    """О курсе"""
    await callback.message.edit_text(
        messages.ABOUT_COURSE,
        reply_markup=get_back_button()
    )
    await callback.answer()

@router.message(F.text == messages.BTN_ABOUT_COURSE)
async def show_about_course_msg(message: Message):
    """О курсе через кнопку"""
    await message.answer(
        messages.ABOUT_COURSE,
        reply_markup=get_back_button()
    )

@router.callback_query(F.data == "referral_info")
async def show_referral_info(callback: CallbackQuery):
    """Реферальная программа"""
    user_id = callback.from_user.id
    
    async with db_manager.get_session() as session:
        # Проверяем, есть ли заявка
        result = await session.execute(
            select(Application).where(Application.user_id == user_id)
        )
        application = result.scalar_one_or_none()
        
        if not application:
            await callback.answer(
                "❌ Реферальная программа доступна только после подачи заявки!",
                show_alert=True
            )
            return
        
        # Получаем статистику рефералов
        result = await session.execute(
            select(func.count(Referral.id)).where(Referral.referrer_id == user_id)
        )
        total_referrals = result.scalar() or 0
        
        # Подсчитываем завершивших 50%
        result = await session.execute(
            select(func.count(Referral.id)).where(
                Referral.referrer_id == user_id,
                Referral.status == 'completed'
            )
        )
        completed_referrals = result.scalar() or 0
        
        earned = completed_referrals * 50
        pending = (total_referrals - completed_referrals) * 50
        
        bot_info = await callback.bot.get_me()
        referral_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
        
        await callback.message.edit_text(
            messages.REFERRAL_STATS.format(
                total_referrals=total_referrals,
                completed_referrals=completed_referrals,
                earned=earned,
                pending=pending,
                referral_link=referral_link
            ),
            reply_markup=get_back_button()
        )
    
    await callback.answer()

@router.callback_query(F.data == "my_referrals")
async def show_my_referrals_callback(callback: CallbackQuery):
    """Мои рефералы через callback"""
    user_id = callback.from_user.id
    
    async with db_manager.get_session() as session:
        # Проверяем, есть ли заявка
        result = await session.execute(
            select(Application).where(Application.user_id == user_id)
        )
        application = result.scalar_one_or_none()
        
        if not application:
            await callback.answer(
                "❌ У вас еще нет рефералов. Сначала подайте заявку на курс!",
                show_alert=True
            )
            return
        
        # Получаем список рефералов
        result = await session.execute(
            select(Referral).where(Referral.referrer_id == user_id)
        )
        referrals = result.scalars().all()
        
        if not referrals:
            bot_info = await callback.bot.get_me()
            referral_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
            
            text = "У вас пока нет рефералов 😔\n\n"
            text += "Поделитесь вашей ссылкой с друзьями:\n"
            text += f"{referral_link}\n\n"
            text += "Когда они пройдут 50% курса, вы оба получите по 50€!"
        else:
            text = f"📊 Ваши рефералы ({len(referrals)}):\n\n"
            
            for i, ref in enumerate(referrals, 1):
                status_emoji = "✅" if ref.status == 'completed' else "⏳"
                text += f"{i}. {status_emoji} Реферал #{ref.referred_id}\n"
            
            text += f"\n✅ Завершили курс: {sum(1 for r in referrals if r.status == 'completed')}"
            text += f"\n⏳ В процессе: {sum(1 for r in referrals if r.status != 'completed')}"
        
        await callback.message.edit_text(text, reply_markup=get_back_button())
        await callback.answer()


@router.message(F.text == messages.BTN_REFERRAL)
async def show_referral_msg(message: Message):
    """Реферальная программа через кнопку"""
    user_id = message.from_user.id
    
    async with db_manager.get_session() as session:
        # Проверяем, есть ли заявка
        result = await session.execute(
            select(Application).where(Application.user_id == user_id)
        )
        application = result.scalar_one_or_none()
        
        if not application:
            await message.answer(
                "❌ Реферальная программа доступна только после подачи заявки на курс.\n\n"
                "Используйте кнопку \"🚀 Записаться на курс\" в главном меню!"
            )
            return
        
        # Получаем статистику рефералов
        result = await session.execute(
            select(func.count(Referral.id)).where(Referral.referrer_id == user_id)
        )
        total_referrals = result.scalar() or 0
        
        # Подсчитываем завершивших 50%
        result = await session.execute(
            select(func.count(Referral.id)).where(
                Referral.referrer_id == user_id,
                Referral.status == 'completed'
            )
        )
        completed_referrals = result.scalar() or 0
        
        earned = completed_referrals * 50
        pending = (total_referrals - completed_referrals) * 50
        
        bot_info = await message.bot.get_me()
        referral_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
        
        await message.answer(
            messages.REFERRAL_STATS.format(
                total_referrals=total_referrals,
                completed_referrals=completed_referrals,
                earned=earned,
                pending=pending,
                referral_link=referral_link
            ),
            reply_markup=get_back_button()
        )

@router.message(F.text == messages.BTN_MY_REFERRALS)
async def show_my_referrals(message: Message):
    """Мои рефералы"""
    user_id = message.from_user.id
    
    async with db_manager.get_session() as session:
        # Проверяем, есть ли заявка
        result = await session.execute(
            select(Application).where(Application.user_id == user_id)
        )
        application = result.scalar_one_or_none()
        
        if not application:
            await message.answer(
                "❌ У вас еще нет рефералов.\n\n"
                "Сначала подайте заявку на курс!"
            )
            return
        
        # Получаем список рефералов
        result = await session.execute(
            select(Referral).where(Referral.referrer_id == user_id)
        )
        referrals = result.scalars().all()
        
        if not referrals:
            bot_info = await message.bot.get_me()
            referral_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
            
            await message.answer(
                f"У вас пока нет рефералов 😔\n\n"
                f"Поделитесь вашей ссылкой с друзьями:\n"
                f"{referral_link}\n\n"
                f"Когда они пройдут 50% курса, вы оба получите по 50€!"
            )
        else:
            text = f"📊 Ваши рефералы ({len(referrals)}):\n\n"
            
            for i, ref in enumerate(referrals, 1):
                status_emoji = "✅" if ref.status == 'completed' else "⏳"
                text += f"{i}. {status_emoji} Реферал #{ref.referred_id}\n"
            
            text += f"\n✅ Завершили курс: {sum(1 for r in referrals if r.status == 'completed')}"
            text += f"\n⏳ В процессе: {sum(1 for r in referrals if r.status != 'completed')}"
            
            await message.answer(text)
