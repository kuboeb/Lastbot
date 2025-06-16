"""
Обработчик команды /start с исправленным сохранением fbclid
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
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username
    
    # ВАЖНО: Сначала обрабатываем fbclid до работы с БД
    command_args = message.text.strip().split(maxsplit=1)
    start_param = command_args[1] if len(command_args) > 1 else None
    
    # Логирование для отладки
    logger.info(f"User {user_id} started with param: {start_param}")
    
    # Обработка fbclid если есть
    if start_param and '__fbclid_' in start_param:
        try:
            fbclid = start_param.split('__fbclid_')[1]
            logger.info(f"Found fbclid for user {user_id}: {fbclid}")
            save_user_fbclid(user_id, fbclid, start_param)
        except Exception as e:
            logger.error(f"Error processing fbclid: {e}")
    
    # Теперь обрабатываем остальную логику
    referrer_id = None
    source_code = None
    
    if start_param:
        # Проверяем реферальную ссылку
        if start_param.startswith('ref_'):
            try:
                referrer_id = int(start_param[4:])
            except ValueError:
                pass
        
        # Проверяем источник трафика
        elif start_param.startswith('src_'):
            # Извлекаем код источника (до первого __)
            source_code = start_param.split('__')[0][4:]
    
    # Далее идет вся остальная логика работы с БД...
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
                    logger.info(f"User {user_id} came from source: {source.name}")
            
            # Если есть реферер, создаем запись
            if referrer_id and referrer_id != user_id:
                referral = Referral(
                    referrer_id=referrer_id,
                    referred_id=user_id,
                    created_at=current_time
                )
                session.add(referral)
                logger.info(f"User {user_id} was referred by {referrer_id}")
            
            session.add(user)
            await save_user_action(session, user_id, 'start')
        else:
            user.last_activity = current_time
            await save_user_action(session, user_id, 'return')
        
        # Проверяем наличие заявки
        result = await session.execute(
            select(Application).where(Application.user_id == user_id)
        )
        has_application = result.scalar_one_or_none() is not None
        
        # Отправляем соответствующее сообщение
        if has_application:
            welcome_text = await get_text('welcome_back', session)
            referral_link = f"https://t.me/{(await message.bot.get_me()).username}?start=ref_{user_id}"
            welcome_text = welcome_text.format(referral_link=referral_link)
            
            await message.answer(
                welcome_text,
                reply_markup=get_main_menu_existing_user()
            )
            await message.answer(
                "Выберите действие:",
                reply_markup=get_reply_keyboard_existing_user()
            )
        else:
            welcome_text = await get_text('welcome_new', session)
            
            await message.answer(
                welcome_text,
                reply_markup=get_main_menu_new_user()
            )
            await message.answer(
                "Выберите действие:",
                reply_markup=get_reply_keyboard_new_user()
            )

# Остальные обработчики...
