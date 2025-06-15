from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    """Состояния процесса регистрации"""
    
    # Ожидание имени и фамилии
    waiting_for_name = State()
    
    # Ожидание страны
    waiting_for_country = State()
    
    # Ожидание телефона
    waiting_for_phone = State()
    
    # Ожидание выбора времени
    waiting_for_time = State()
    
    # Подтверждение данных
    confirming_data = State()

class ReferralStates(StatesGroup):
    """Состояния для работы с рефералами"""
    
    # Просмотр статистики
    viewing_stats = State()
