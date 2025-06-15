"""
Утилиты для работы с датами и временем
"""
from datetime import datetime
from typing import Optional

def normalize_datetime(dt: Optional[datetime]) -> Optional[datetime]:
    """Нормализует datetime объект, убирая timezone информацию"""
    if dt is None:
        return None
    
    # Если есть timezone info, конвертируем в naive datetime
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    
    return dt

def get_current_datetime() -> datetime:
    """Возвращает текущую дату и время без timezone"""
    return datetime.now()
