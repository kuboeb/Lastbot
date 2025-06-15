"""
Загрузка текстов из базы данных
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class TextManager:
    """Менеджер текстов из БД"""
    
    def __init__(self):
        self._cache: Dict[str, str] = {}
        self._loaded = False
    
    def get_db_connection(self):
        """Получить подключение к БД"""
        return psycopg2.connect(
            host='localhost',
            database='crypto_course_db',
            user='cryptobot',
            password='kuboeb1A',
            cursor_factory=RealDictCursor
        )
    
    def load_all_texts(self):
        """Загрузить все тексты из БД в кэш"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT key, text FROM bot_texts")
            texts = cur.fetchall()
            cur.close()
            conn.close()
            
            self._cache = {row['key']: row['text'] for row in texts}
            self._loaded = True
            logger.info(f"Loaded {len(self._cache)} texts from database")
        except Exception as e:
            logger.error(f"Error loading texts from database: {e}")
    
    def get(self, key: str, default: str = "") -> str:
        """Получить текст по ключу"""
        if not self._loaded:
            self.load_all_texts()
        
        text = self._cache.get(key, default)
        return text if text else default
    
    def reload(self):
        """Перезагрузить тексты из БД"""
        self._cache.clear()
        self._loaded = False
        self.load_all_texts()

# Глобальный экземпляр
text_manager = TextManager()

# Функция для обратной совместимости
def get_text(key: str, default: str = "") -> str:
    """Получить текст по ключу"""
    return text_manager.get(key, default)
