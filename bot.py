#!/usr/bin/env python3
import sys
sys.path.append("/home/Lastbot")
"""
Главный файл Telegram бота для записи на курс криптовалют
"""

import asyncio
import logging
import sys
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from config import config
from database import db_manager
from handlers import start, registration, info
from middlewares.tracking import TrackingMiddleware
from middlewares.antiflood import AntifloodMiddleware
from middlewares.logging import LoggingMiddleware

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Регистрация админских команд
try:
    from admin_commands import admin_router
    dp.include_router(admin_router)
    logger.info("Admin commands registered")
except Exception as e:
    logger.error(f"Failed to register admin commands: {e}")


# Регистрируем middleware
dp.message.middleware(LoggingMiddleware())
dp.message.middleware(AntifloodMiddleware())
dp.message.middleware(TrackingMiddleware())
dp.callback_query.middleware(LoggingMiddleware())

async def set_bot_commands():
    """Устанавливает команды бота"""
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="apply", description="Записаться на курс"),
        BotCommand(command="ref", description="Реферальная ссылка"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="program", description="Программа курса"),
        BotCommand(command="reviews", description="Отзывы учеников"),
    ]
    await bot.set_my_commands(commands)

async def on_startup():
    """Действия при запуске бота"""
    logger.info("Bot starting...")
    
    # Подключаемся к БД
    await db_manager.connect()
    logger.info("Database connected")
    
    # Устанавливаем команды
    await set_bot_commands()
    
    # Регистрируем обработчики
    dp.include_router(start.router)
    dp.include_router(registration.router)
    dp.include_router(info.router)
    
    logger.info("Bot started successfully")

async def on_shutdown():
    """Действия при остановке бота"""
    logger.info("Bot shutting down...")
    
    # Закрываем соединение с БД
    await db_manager.disconnect()
    
    # Закрываем сессию бота
    await bot.session.close()
    
    logger.info("Bot stopped")

async def main():
    """Основная функция"""
    try:
        # Выполняем действия при запуске
        await on_startup()
        
        # Запускаем polling
        logger.info("Starting polling...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Bot crashed with error: {e}")
        raise
    finally:
        # Выполняем действия при остановке
        await on_shutdown()

if __name__ == "__main__":

# scheduler.start()
# print("✅ Планировщик запущен - сценарии будут отправляться в 12:00 GMT+3")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

