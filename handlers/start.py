from sqlalchemy import select
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
import re
import logging

from database import db_manager, BotUser, Application, TrafficSource, Referral, UserAction
from keyboards.keyboards import (
    get_main_menu_new_user, 
    get_main_menu_existing_user,
    get_reply_keyboard_new_user,
    get_reply_keyboard_existing_user
)
from utils import messages
from config import config

router = Router()
logger = logging.getLogger(__name__)

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Парсим параметры команды start
    args = message.text.split()
    referrer_id = None
    source_code = None
    
    if len(args) > 1:
        param = args[1]
        
        # Проверяем реферальную ссылку
        if param.startswith('ref'):
            match = re.match(r'ref(\d+)', param)
            if match:
                referrer_id = int(match.group(1))
                logger.info(f"User {user_id} came from referral {referrer_id}")
        
        # Проверяем источник трафика
        elif param.startswith('src_'):
            source_code = param[4:]
            logger.info(f"User {user_id} came from source {source_code}")
    
    async with db_manager.get_session() as session:
        user = (await session.execute(select(BotUser).where(BotUser.user_id == user_id))).scalar_one_or_none()
        user = (await session.execute(select(BotUser).where(BotUser.user_id == user_id))).scalar_one_or_none()
        
        if not user:
            # Создаем нового пользователя
            user = BotUser(
                user_id=user_id,
                username=username
            )
            
            # Если есть источник трафика, находим его
            if source_code:
                source = await session.query(TrafficSource).filter_by(
                    tracking_code=source_code,
                    is_active=True
                ).first()
                if source:
                    user.source_id = source.id
            
            session.add(user)
            
            # Если есть реферер, создаем запись
            if referrer_id and referrer_id != user_id:
                referral = Referral(
                    referrer_id=referrer_id,
                    referred_id=user_id
                )
                session.add(referral)
                
                # Отправляем уведомление рефереру
                await message.bot.send_message(
                    referrer_id,
                    f"🎉 По вашей ссылке зарегистрировался новый пользователь!"
                )
        
        # Логируем действие
        action = UserAction(user_id=user_id, action="start")
        session.add(action)
        
        # Обновляем последнюю активность
        user.last_activity = message.date
        
        # Проверяем, есть ли заявка
        application = await session.query(Application).filter_by(user_id=user_id).first()
        
        if application:
            # Пользователь уже подавал заявку
            referral_link = f"https://t.me/{(await message.bot.get_me()).username}?start=ref{user_id}"
            
            await message.answer(
                messages.WELCOME_EXISTING_USER.format(referral_link=referral_link),
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
                referrer = (await session.execute(select(BotUser).where(BotUser.user_id == referrer_id))).scalar_one_or_none()
                if referrer:
                    referrer_name = referrer.username or "пользователя"
                    await message.answer(
                        f"🎁 Вы пришли по приглашению от {referrer_name}!\n"
                        f"После прохождения 50% курса вы оба получите по 50€ 💰"
                    )
            
            await message.answer(
                messages.WELCOME_NEW_USER,
                reply_markup=get_reply_keyboard_new_user()
            )
            await message.answer(
                "Выберите действие:",
                reply_markup=get_main_menu_new_user()
            )

@router.message(F.text == messages.BTN_MAIN_MENU)
async def main_menu(message: Message, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    
    async with db_manager.get_session() as session:
        application = await session.query(Application).filter_by(
            user_id=message.from_user.id
        ).first()
        
        if application:
            await message.answer(
                "Главное меню:",
                reply_markup=get_main_menu_existing_user()
            )
        else:
            await message.answer(
                "Главное меню:",
                reply_markup=get_main_menu_new_user()
            )

@router.message(F.text == messages.BTN_ABOUT)
async def about_course(message: Message):
    """Информация о курсе"""
    await message.answer(messages.ABOUT_COURSE)

@router.message(F.text == "💰 Реферальная ссылка")
async def referral_link(message: Message):
    """Показать реферальную ссылку"""
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
        
        # Считаем статистику
        referrals_count = await session.query(Referral).filter_by(
            referrer_id=user_id
        ).count()
        
        await message.answer(
            f"💰 Ваша реферальная ссылка:\n"
            f"{referral_link}\n\n"
            f"Приглашено друзей: {referrals_count}\n\n"
            f"Поделитесь ссылкой с друзьями и получите по 50€ за каждого!"
        )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Команда помощи"""
    help_text = """🤖 Доступные команды:

/start - Главное меню
/apply - Быстрая запись на курс
/ref - Моя реферальная ссылка
/program - Программа курса
/reviews - Отзывы учеников
/help - Это сообщение

По всем вопросам обращайтесь к @support"""
    
    await message.answer(help_text)
