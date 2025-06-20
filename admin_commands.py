"""
Админские команды для бота
"""
from aiogram import types, Router
from config import ADMIN_ID
from utils.db_texts import text_manager
import logging

logger = logging.getLogger(__name__)

# Создаем роутер для админских команд
admin_router = Router()

@admin_router.message(lambda message: message.text == '/reload_texts' and message.from_user.id == ADMIN_ID)
async def reload_texts_command(message: types.Message):
    """Перезагрузить тексты из БД"""
    try:
        text_manager.reload()
        await message.reply("✅ Тексты успешно перезагружены из БД")
        logger.info(f"Admin {message.from_user.id} reloaded texts")
    except Exception as e:
        await message.reply(f"❌ Ошибка при перезагрузке текстов: {e}")
        logger.error(f"Error reloading texts: {e}")
