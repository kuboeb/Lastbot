"""
Обработчик процесса регистрации на курс
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
import re
from datetime import datetime

from database import db_manager, Application, BotUser, Referral, UserAction
from keyboards.keyboards import (
    get_time_selection_keyboard,
    get_confirmation_keyboard,
    get_back_button,
    get_main_menu_existing_user,
    get_registration_keyboard,
    get_reply_keyboard_existing_user
)
from utils import messages
from utils.datetime_utils import get_current_datetime
from config import config

router = Router(name="registration")

class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_country = State()
    waiting_for_phone = State()
    waiting_for_time = State()
    confirmation = State()

async def save_user_action(session, user_id: int, action: str):
    """Сохраняет действие пользователя"""
    user_action = UserAction(
        user_id=user_id,
        action=action,
        created_at=get_current_datetime()
    )
    session.add(user_action)

@router.callback_query(F.data == "apply")
async def start_registration_callback(callback: CallbackQuery, state: FSMContext):
    """Начало регистрации через inline кнопку"""
    await start_registration(callback.message, state)
    await callback.answer()

@router.message(F.text == messages.BTN_APPLY)
async def start_registration_msg(message: Message, state: FSMContext):
    """Начало регистрации через reply кнопку"""
    await start_registration(message, state)

async def start_registration(message: Message, state: FSMContext):
    """Начало процесса регистрации"""
    user_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id
    
    async with db_manager.get_session() as session:
        # Проверяем, есть ли уже заявка
        result = await session.execute(
            select(Application).where(Application.user_id == user_id)
        )
        existing_app = result.scalar_one_or_none()
        
        if existing_app:
            await message.answer(
                messages.ALREADY_APPLIED,
                reply_markup=get_back_button()
            )
            return
        
        # Сохраняем действие
        await save_user_action(session, user_id, 'begin_registration')
        await session.commit()
    
    await state.set_state(RegistrationStates.waiting_for_name)
    await message.answer(messages.ASK_NAME, reply_markup=get_registration_keyboard())

@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка имени"""
    # Проверяем, не нажата ли кнопка "Назад"
    if message.text == messages.BTN_BACK:
        await state.clear()
        await message.answer("Регистрация отменена.")
        # Вызываем команду /start
        from handlers.start import cmd_start
        await cmd_start(message, state)
        return
    
    name = message.text.strip()
    
    # Проверка имени
    if len(name) < 2:
        await message.answer("❌ Имя слишком короткое. Введите полное имя и фамилию:")
        return
    
    if not all(c.isalpha() or c.isspace() for c in name):
        await message.answer("❌ Имя может содержать только буквы. Попробуйте еще раз:")
        return
    
    await state.update_data(full_name=name)
    
    # Сохраняем действие
    async with db_manager.get_session() as session:
        await save_user_action(session, message.from_user.id, 'enter_name')
        await session.commit()
    
    await state.set_state(RegistrationStates.waiting_for_country)
    await message.answer(messages.ASK_COUNTRY, reply_markup=get_registration_keyboard())

@router.message(RegistrationStates.waiting_for_country)
async def process_country(message: Message, state: FSMContext):
    """Обработка страны"""
    # Проверяем, не нажата ли кнопка "Назад"
    if message.text == messages.BTN_BACK:
        await state.set_state(RegistrationStates.waiting_for_name)
        await message.answer(messages.ASK_NAME, reply_markup=get_registration_keyboard())
        return
    
    country = message.text.strip()
    
    # Проверка страны
    if len(country) < 2:
        await message.answer("❌ Название страны слишком короткое. Введите полное название:")
        return
    
    # Проверка на Украину
    ukraine_variants = ['украина', 'ukraine', 'україна', 'ua', 'укр']
    if any(variant in country.lower() for variant in ukraine_variants):
        await message.answer(messages.UKRAINE_RESTRICTION)
        await state.clear()
        # Возвращаемся в главное меню
        from handlers.start import cmd_start
        await cmd_start(message, state)
        return
    
    await state.update_data(country=country)
    
    # Сохраняем действие
    async with db_manager.get_session() as session:
        await save_user_action(session, message.from_user.id, 'enter_country')
        await session.commit()
    
    await state.set_state(RegistrationStates.waiting_for_phone)
    await message.answer(messages.ASK_PHONE, reply_markup=get_registration_keyboard())

@router.message(RegistrationStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обработка телефона"""
    # Проверяем, не нажата ли кнопка "Назад"
    if message.text == messages.BTN_BACK:
        await state.set_state(RegistrationStates.waiting_for_country)
        await message.answer(messages.ASK_COUNTRY, reply_markup=get_registration_keyboard())
        return
    
    phone = message.text.strip()
    
    # Убираем все символы кроме цифр и +
    phone = re.sub(r'[^\d+]', '', phone)
    
    # Проверка телефона
    if not phone.startswith('+'):
        await message.answer("❌ Пожалуйста, добавьте код страны, например: +49 для Германии")
        return
    
    if len(phone) < 10 or len(phone) > 15:
        await message.answer("❌ Неверный формат номера. Введите номер с кодом страны:")
        return
    
    await state.update_data(phone=phone)
    
    # Сохраняем действие
    async with db_manager.get_session() as session:
        await save_user_action(session, message.from_user.id, 'enter_phone')
        await session.commit()
    
    await state.set_state(RegistrationStates.waiting_for_time)
    await message.answer(
        messages.ASK_TIME,
        reply_markup=get_time_selection_keyboard()
    )

@router.callback_query(RegistrationStates.waiting_for_time, F.data.startswith("time_"))
async def process_time(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора времени"""
    time_slot = callback.data.replace("time_", "").replace("_", " - ")
    await state.update_data(preferred_time=time_slot)
    
    # Сохраняем действие
    async with db_manager.get_session() as session:
        await save_user_action(session, callback.from_user.id, 'enter_time')
        await session.commit()
    
    # Получаем все данные
    data = await state.get_data()
    
    confirmation_text = messages.CONFIRMATION_TEXT.format(
        name=data['full_name'],
        country=data['country'],
        phone=data['phone'],
        time=time_slot
    )
    
    await state.set_state(RegistrationStates.confirmation)
    await callback.message.edit_text(
        confirmation_text,
        reply_markup=get_confirmation_keyboard()
    )
    await callback.answer()

@router.callback_query(RegistrationStates.confirmation, F.data == "confirm")
async def confirm_registration(callback: CallbackQuery, state: FSMContext):
    """Подтверждение регистрации"""
    user_id = callback.from_user.id
    data = await state.get_data()
    
    async with db_manager.get_session() as session:
        # Обновляем информацию о пользователе
        result = await session.execute(
            select(BotUser).where(BotUser.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            user.has_application = True
        
        # Получаем реферера если есть
        result = await session.execute(
            select(Referral).where(Referral.referred_id == user_id)
        )
        referral = result.scalar_one_or_none()
        
        # Создаем заявку
        application = Application(
            user_id=user_id,
            full_name=data['full_name'],
            country=data['country'],
            phone=data['phone'],
            preferred_time=data['preferred_time'],
            referrer_id=referral.referrer_id if referral else None,
            source_id=user.source_id if user else None,
            created_at=get_current_datetime()
        )
        
        session.add(application)
        
        # Сохраняем действие
        await save_user_action(session, user_id, 'completed')
        
        await session.commit()
    
    # Отправляем уведомление админу
    bot_info = await callback.bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    
    admin_message = messages.ADMIN_NOTIFICATION.format(
        name=data['full_name'],
        country=data['country'],
        phone=data['phone'],
        time=data['preferred_time'],
        date=get_current_datetime().strftime('%d.%m.%Y %H:%M'),
        username=f"@{callback.from_user.username}" if callback.from_user.username else "Не указан",
        invited="Да" if referral else "Нет"
    )
    
    try:
        await callback.bot.send_message(config.ADMIN_ID, admin_message)
    except Exception as e:
        print(f"Ошибка отправки уведомления админу: {e}")
    
    # Отправляем финальное сообщение пользователю
    await callback.message.answer(
        messages.REGISTRATION_COMPLETE.format(
            name=data['full_name'],
            referral_link=referral_link
        ),
        reply_markup=get_reply_keyboard_existing_user()
    )
    
    # Показываем главное меню
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_main_menu_existing_user()
    )
    
    # Удаляем сообщение с подтверждением
    await callback.message.delete()
    
    await state.clear()
    await callback.answer("✅ Заявка успешно отправлена!", show_alert=True)

@router.callback_query(RegistrationStates.confirmation, F.data == "edit")
async def edit_registration(callback: CallbackQuery, state: FSMContext):
    """Редактирование данных"""
    await state.set_state(RegistrationStates.waiting_for_name)
    await callback.message.answer(messages.ASK_NAME, reply_markup=get_registration_keyboard())
    await callback.answer()

@router.message(F.text == messages.BTN_BACK)
async def handle_back_button(message: Message, state: FSMContext):
    """Обработка кнопки Назад вне состояний регистрации"""
    current_state = await state.get_state()
    
    if not current_state:
        # Если нет активного состояния, возвращаемся в главное меню
        from handlers.start import cmd_start
        await cmd_start(message, state)
