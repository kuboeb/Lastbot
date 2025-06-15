from sqlalchemy import select
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime
import re
import logging

from database import db_manager, BotUser, Application, UserAction, TrafficSource
from states.registration import RegistrationStates
from keyboards.keyboards import (
    get_back_keyboard, 
    get_time_selection_keyboard,
    get_confirmation_keyboard,
    get_share_referral_keyboard,
    get_reply_keyboard_new_user, 
    get_main_menu_new_user, 
    get_reply_keyboard_existing_user
)
from utils import messages
from utils.validators import validate_phone, validate_name, validate_country, format_phone
from config import config

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "apply")
@router.message(Command("apply"))
async def start_registration(update: Message | CallbackQuery, state: FSMContext):
    """Начало процесса регистрации"""
    if isinstance(update, CallbackQuery):
        message = update.message
        user_id = update.from_user.id
        await update.answer()
    else:
        message = update
        user_id = update.from_user.id
    
    # Проверяем, есть ли уже заявка
    async with db_manager.get_session() as session:
        existing_app = await session.query(Application).filter_by(user_id=user_id).first()
        
        if existing_app:
            await message.answer(messages.ERROR_ALREADY_REGISTERED)
            return
        
        # Логируем начало регистрации
        action = UserAction(user_id=user_id, action="begin_registration")
        session.add(action)
    
    # Запрашиваем имя
    await message.answer(
        messages.REGISTRATION_NAME,
        reply_markup=get_back_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_name)

@router.message(RegistrationStates.waiting_for_name, F.text == messages.BTN_BACK)
async def back_from_name(message: Message, state: FSMContext):
    """Возврат из ввода имени"""
    await state.clear()
    await message.answer(
        "Регистрация отменена. Возвращаемся в главное меню.",
        reply_markup=get_reply_keyboard_new_user()
    )
    await message.answer(
        "Выберите действие:",
        reply_markup=get_main_menu_new_user()
    )

@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка имени и фамилии"""
    full_name = message.text.strip()
    
    # Валидация
    is_valid, error_msg = validate_name(full_name)
    if not is_valid:
        await message.answer(error_msg)
        return
    
    # Сохраняем в состояние
    await state.update_data(full_name=full_name)
    
    # Логируем действие
    async with db_manager.get_session() as session:
        action = UserAction(user_id=message.from_user.id, action="enter_name")
        session.add(action)
    
    # Запрашиваем страну
    await message.answer(
        messages.REGISTRATION_COUNTRY,
        reply_markup=get_back_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_country)

@router.message(RegistrationStates.waiting_for_country, F.text == messages.BTN_BACK)
async def back_from_country(message: Message, state: FSMContext):
    """Возврат к вводу имени"""
    await message.answer(
        messages.REGISTRATION_NAME,
        reply_markup=get_back_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_name)

@router.message(RegistrationStates.waiting_for_country)
async def process_country(message: Message, state: FSMContext):
    """Обработка страны"""
    country = message.text.strip()
    
    # Валидация
    is_valid, error_msg = validate_country(country)
    if not is_valid:
        await message.answer(error_msg)
        return
    
    # Сохраняем в состояние
    await state.update_data(country=country)
    
    # Логируем действие
    async with db_manager.get_session() as session:
        action = UserAction(user_id=message.from_user.id, action="enter_country")
        session.add(action)
    
    # Запрашиваем телефон
    await message.answer(
        messages.REGISTRATION_PHONE,
        reply_markup=get_back_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_phone)

@router.message(RegistrationStates.waiting_for_phone, F.text == messages.BTN_BACK)
async def back_from_phone(message: Message, state: FSMContext):
    """Возврат к вводу страны"""
    await message.answer(
        messages.REGISTRATION_COUNTRY,
        reply_markup=get_back_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_country)

@router.message(RegistrationStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обработка телефона"""
    phone = message.text.strip()
    
    # Форматируем телефон
    phone = format_phone(phone)
    
    # Валидация
    is_valid, error_msg = validate_phone(phone)
    if not is_valid:
        await message.answer(error_msg)
        return
    
    # Сохраняем в состояние
    await state.update_data(phone=phone)
    
    # Логируем действие
    async with db_manager.get_session() as session:
        action = UserAction(user_id=message.from_user.id, action="enter_phone")
        session.add(action)
    
    # Запрашиваем время
    await message.answer(
        messages.REGISTRATION_TIME,
        reply_markup=get_time_selection_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_time)

@router.callback_query(RegistrationStates.waiting_for_time, F.data.startswith("time_"))
async def process_time(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора времени"""
    time_map = {
        "time_9_12": "9:00 - 12:00",
        "time_12_15": "12:00 - 15:00",
        "time_15_18": "15:00 - 18:00",
        "time_18_21": "18:00 - 21:00"
    }
    
    preferred_time = time_map.get(callback.data, "9:00 - 12:00")
    await state.update_data(preferred_time=preferred_time)
    
    # Логируем действие
    async with db_manager.get_session() as session:
        action = UserAction(user_id=callback.from_user.id, action="enter_time")
        session.add(action)
    
    # Показываем данные для подтверждения
    data = await state.get_data()
    confirmation_text = messages.REGISTRATION_CONFIRM.format(
        full_name=data['full_name'],
        country=data['country'],
        phone=data['phone'],
        preferred_time=data['preferred_time']
    )
    
    await callback.message.edit_text(confirmation_text)
    await callback.message.answer(
        "Подтвердите данные:",
        reply_markup=get_confirmation_keyboard()
    )
    await state.set_state(RegistrationStates.confirming_data)
    await callback.answer()

@router.message(RegistrationStates.confirming_data, F.text == messages.BTN_BACK)
async def back_from_confirmation(message: Message, state: FSMContext):
    """Возврат к выбору времени"""
    await message.answer(
        messages.REGISTRATION_TIME,
        reply_markup=get_time_selection_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_time)

@router.message(RegistrationStates.confirming_data, F.text == messages.BTN_EDIT)
async def edit_data(message: Message, state: FSMContext):
    """Редактирование данных - начинаем сначала"""
    await message.answer(
        "Давайте заполним данные заново.\n\n" + messages.REGISTRATION_NAME,
        reply_markup=get_back_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_name)

@router.message(RegistrationStates.confirming_data, F.text == messages.BTN_CONFIRM)
async def confirm_registration(message: Message, state: FSMContext):
    """Подтверждение и сохранение заявки"""
    user_id = message.from_user.id
    data = await state.get_data()
    
    async with db_manager.get_session() as session:
        # Получаем пользователя
        user = (await session.execute(select(BotUser).where(BotUser.user_id == user_id))).scalar_one_or_none()
        
        # Создаем заявку
        application = Application(
            user_id=user_id,
            full_name=data['full_name'],
            country=data['country'],
            phone=data['phone'],
            preferred_time=data['preferred_time'],
            source_id=user.source_id if user else None
        )
        
        # Проверяем реферала
        from database import Referral
        referral = await session.query(Referral).filter_by(referred_id=user_id).first()
        if referral:
            application.referrer_id = referral.referrer_id
        
        session.add(application)
        
        # Обновляем статус пользователя
        if user:
            user.has_application = True
        
        # Логируем завершение
        action = UserAction(user_id=user_id, action="complete_registration")
        session.add(action)
        
        await session.commit()
        
        # Отправляем уведомление админу
        admin_message = f"""🆕 Новая заявка на курс!

👤 Имя: {data['full_name']}
🌍 Страна: {data['country']}
📱 Телефон: {data['phone']}
⏰ Удобное время: {data['preferred_time']}
📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}
🔗 Username: @{message.from_user.username or 'отсутствует'}
👥 Приглашен: {'Да' if referral else 'Нет'}"""
        
        await message.bot.send_message(config.ADMIN_ID, admin_message)
        
        # Отправляем конверсию если есть источник
        if user and user.source_id:
            source = await session.get(TrafficSource, user.source_id)
            if source:
                from utils.conversions import ConversionSender
                await ConversionSender.send_lead_conversion(application, source)
    
    # Отправляем успешное сообщение
    bot_username = (await message.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref{user_id}"
    
    await message.answer(
        messages.REGISTRATION_SUCCESS.format(referral_link=referral_link),
        reply_markup=get_reply_keyboard_existing_user()
    )
    
    await message.answer(
        "Поделитесь ссылкой:",
        reply_markup=get_share_referral_keyboard(referral_link)
    )
    
    # Очищаем состояние
    await state.clear()
