"""
Загрузчик текстов из админ-панели
"""
import aiohttp
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class TextLoader:
    """Класс для загрузки текстов из админ-панели"""
    
    def __init__(self, api_url: str = "http://localhost:8000/api/texts", api_key: str = "internal-bot-key-2024"):
        self.api_url = api_url
        self.api_key = api_key
        self._cache: Dict[str, str] = {}
        self._default_texts: Dict[str, str] = {}
    
    async def load_text(self, key: str) -> Optional[str]:
        """Загрузить текст по ключу"""
        # Сначала проверяем кэш
        if key in self._cache:
            return self._cache[key]
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/{key}",
                    headers={"X-API-Key": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        text = data.get('text')
                        if text:
                            self._cache[key] = text
                            return text
        except Exception as e:
            logger.error(f"Error loading text {key}: {e}")
        
        # Возвращаем дефолтный текст если не удалось загрузить
        return self._default_texts.get(key)
    
    def set_default(self, key: str, text: str):
        """Установить дефолтный текст"""
        self._default_texts[key] = text
    
    def clear_cache(self):
        """Очистить кэш"""
        self._cache.clear()

# Глобальный экземпляр
text_loader = TextLoader()

# Устанавливаем дефолтные тексты из messages.py
from . import messages

text_loader.set_default('WELCOME_NEW_USER', messages.WELCOME_NEW_USER)
text_loader.set_default('WELCOME_EXISTING_USER', messages.WELCOME_EXISTING_USER)
text_loader.set_default('ASK_NAME', messages.ASK_NAME)
text_loader.set_default('ASK_COUNTRY', messages.ASK_COUNTRY)
text_loader.set_default('ASK_PHONE', messages.ASK_PHONE)
text_loader.set_default('ASK_TIME', messages.ASK_TIME)
text_loader.set_default('ALREADY_APPLIED', messages.ALREADY_APPLIED)
text_loader.set_default('UKRAINE_RESTRICTION', messages.UKRAINE_RESTRICTION)
text_loader.set_default('COURSE_PROGRAM', messages.COURSE_PROGRAM)
text_loader.set_default('HELP_MESSAGE', messages.HELP_MESSAGE)
