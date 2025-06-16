"""
Обработчик команды /start и главного меню
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func
import re
import logging
from datetime import datetime

from database import db_manager, BotUser, Application, TrafficSource, UserAction, Referral
from keyboards.keyboards import (
    get_main_menu_new_user,
    get_main_menu_existing_user,
    get_reply_keyboard_new_user,
    get_reply_keyboard_existing_user,
    get_back_button
)
from utils import messages
from utils.db_texts import get_text
from utils.datetime_utils import normalize_datetime, get_current_datetime

from handlers.facebook_utils import save_user_fbclid

router = Router(name="start")
logger = logging.getLogger(__name__)

async def save_user_action(session, user_id: int, action: str):
    """Сохраняет действие пользователя"""
    user_action = UserAction(
        user_id=user_id,
        action=action,
        created_at=get_current_datetime()
    )
    session.add(user_action)

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    
    # Подробное логирование для отладки
    logger.info(f"=== START COMMAND DEBUG ===")
    logger.info(f"User ID: {user_id}")
    logger.info(f"Username: {username}")
    logger.info(f"Full message text: {message.text}")
    logger.info(f"Command args: {command_args}")
    logger.info(f"Start param: {start_param}")
    
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Парсим параметры команды start
    command_args = message.text.strip().split(maxsplit=1)
    start_param = command_args[1] if len(command_args) > 1 else None
    
    referrer_id = None
    source_code = None
    click_id = None
    
    if start_param:
        # Проверяем реферальную ссылку
        if start_param.startswith('ref_'):
            try:
                referrer_id = int(start_param[4:])
            except ValueError:
                pass
        
        # Проверяем источник трафика
        elif start_param.startswith('src_'):
            logger.info(f'Processing source param: {start_param}')
            parts = start_param.split('__')  # Используем двойное подчеркивание как разделитель
            source_code = parts[0][4:]  # Убираем src_
            
            # Извлекаем click_id если есть
            for part in parts[1:]:
                if part.startswith('fbclid_') or part.startswith('gclid_'):
                    click_id = part
                    # Сохраняем fbclid в таблицу user_clicks
                    if part.startswith('fbclid_'):
                        logger.info(f'Found fbclid part: {part}')
                        fbclid_value = part.replace('fbclid_', '')
                        try:
                            save_user_fbclid(user_id, fbclid_value, start_param)
                            logger.info(f"Saved fbclid for user {user_id}: {fbclid_value[:20]}...")
                        except Exception as e:
                            logger.error(f"Failed to save fbclid: {e}")
    
    async with db_manager.get_session() as session:
        # Проверяем/создаем пользователя
        result = await session.execute(select(BotUser).where(BotUser.user_id == user_id))
        user = result.scalar_one_or_none()
        
        current_time = get_current_datetime()
        
        if not user:
            user = BotUser(
                user_id=user_id,
                username=username,
                first_seen=current_time,
                last_activity=current_time
            )
            
            # Если есть источник трафика, находим его
            if source_code:
                result = await session.execute(
                    select(TrafficSource).where(TrafficSource.source_code == source_code)
                )
                source = result.scalar_one_or_none()
                if source:
                    user.source_id = source.id
            
            session.add(user)
            
            # Сохраняем реферала если есть
            if referrer_id and referrer_id != user_id:
                referral = Referral(
                    referrer_id=referrer_id,
                    referred_id=user_id,
                    created_at=current_time
                )
                session.add(referral)
            
            await session.commit()
        else:
            user.last_activity = current_time
            await session.commit()
        
        # Проверяем, есть ли заявка
        result = await session.execute(select(Application).where(Application.user_id == user_id))
        application = result.scalar_one_or_none()
        
        # Сохраняем действие пользователя
        await save_user_action(session, user_id, 'start')
        await session.commit()
        
        if application:
            # Пользователь уже подавал заявку
            referral_link = f"https://t.me/{(await message.bot.get_me()).username}?start=ref_{user_id}"
            
            # Считаем рефералов
            result = await session.execute(
                select(func.count(Referral.id)).where(Referral.referrer_id == user_id)
            )
            referrals_count = result.scalar() or 0
            
            await message.answer(
                get_text("WELCOME_EXISTING_USER", messages.WELCOME_EXISTING_USER).format(
                    referral_link=referral_link,
                    referrals_count=referrals_count
                ),
                reply_markup=get_reply_keyboard_existing_user()
            )
            await message.answer(
                "Выберите действие:",
                reply_markup=get_main_menu_existing_user()
            )
        else:
            # Новый пользователь
            # Проверяем реферала
            if referrer_id:
                result = await session.execute(
                    select(BotUser).where(BotUser.user_id == referrer_id)
                )
                referrer = result.scalar_one_or_none()
                if referrer:
                    referrer_name = referrer.username or "пользователя"
                    await message.answer(
                        f"🎁 Вы пришли по приглашению от {referrer_name}!\n"
                        f"После прохождения 50% курса вы оба получите по 50€ 💰"
                    )
            
            await message.answer(
                get_text("WELCOME_NEW_USER", messages.WELCOME_NEW_USER),
                reply_markup=get_reply_keyboard_new_user()
            )
            await message.answer(
                "Выберите действие:",
                reply_markup=get_main_menu_new_user()
            )

@router.message(F.text == "🏠 Главное меню")
async def main_menu(message: Message, state: FSMContext):
    """Возврат в главное меню - вызывает /start"""
    await cmd_start(message, state)

@router.message(F.text == "💰 Реферальная ссылка")
async def show_referral_link(message: Message):
    """Показать реферальную ссылку"""
    user_id = message.from_user.id
    
    async with db_manager.get_session() as session:
        result = await session.execute(
            select(Application).where(Application.user_id == user_id)
        )
        application = result.scalar_one_or_none()
        
        if application:
            bot_info = await message.bot.get_me()
            referral_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
            
            result = await session.execute(
                select(func.count(Referral.id)).where(Referral.referrer_id == user_id)
            )
            referrals_count = result.scalar() or 0
            
            await message.answer(
                get_text("REFERRAL_INFO", messages.REFERRAL_INFO).format(
                    referral_link=referral_link,
                    referrals_count=referrals_count
                ),
                reply_markup=get_back_button()
            )
        else:
            await message.answer(
                "❌ Реферальная программа доступна только после подачи заявки на курс.\n\n"
                "Используйте кнопку '🚀 Записаться на курс' в меню!"
            )

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню через inline кнопку"""
    await state.clear()
    
    async with db_manager.get_session() as session:
        result = await session.execute(
            select(Application).where(Application.user_id == callback.from_user.id)
        )
        application = result.scalar_one_or_none()
        
        if application:
            await callback.message.edit_text(
                "Главное меню:",
                reply_markup=get_main_menu_existing_user()
            )
        else:
            await callback.message.edit_text(
                "Главное меню:",
                reply_markup=get_main_menu_new_user()
            )
        
        await callback.answer()

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Команда помощи"""
    await message.answer(get_text("HELP_MESSAGE", messages.HELP_MESSAGE))

@router.message(Command("apply"))
async def cmd_apply(message: Message, state: FSMContext):
    """Быстрая команда для записи на курс"""
    from handlers.registration import start_registration
    await start_registration(message, state)

@router.message(Command("ref"))
async def cmd_ref(message: Message):
    """Команда для получения реферальной ссылки"""
    await show_referral_link(message)

@router.message(Command("program"))
async def cmd_program(message: Message):
    """Команда для просмотра программы курса"""
    from handlers.info import show_program
    await show_program(message)

@router.message(Command("reviews"))
async def cmd_reviews(message: Message):
    """Команда для просмотра отзывов"""
    from handlers.info import show_reviews
    await show_reviews(message)

# Временная функция для отладки
def debug_start_params(message_text):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"DEBUG: Full message text: {message_text}")
    if ' ' in message_text:
        parts = message_text.split(' ', 1)
        if len(parts) > 1:
            logger.info(f"DEBUG: Start parameter: {parts[1]}")
    return None
