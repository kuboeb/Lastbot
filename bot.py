import asyncio
import logging
import sys
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import config
from database import db_manager
from handlers import start, registration, info
from middlewares.antiflood import AntifloodMiddleware
from middlewares.tracking import TrackingMiddleware
from middlewares.logging import LoggingMiddleware

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

async def on_startup(app: web.Application) -> None:
    """Действия при запуске бота"""
    logger.info("Bot starting...")
    
    # Подключаемся к базе данных
    await db_manager.connect()
    await db_manager.create_tables()
    
    # Регистрируем middleware
    dp.message.middleware(AntifloodMiddleware())
    dp.message.middleware(TrackingMiddleware())
    dp.message.middleware(LoggingMiddleware())
    
    # Регистрируем обработчики
    dp.include_router(start.router)
    dp.include_router(registration.router)
    dp.include_router(info.router)
    
    # Устанавливаем webhook
    if config.SERVER_DOMAIN:
        webhook_url = f"https://{config.SERVER_DOMAIN}/webhook"
    else:
        webhook_url = f"http://{config.SERVER_IP}:{config.BOT_WEBHOOK_PORT}/webhook"
    
    await bot.set_webhook(webhook_url, secret_token=config.WEBHOOK_SECRET)
    logger.info(f"Webhook set to {webhook_url}")

async def on_shutdown(app: web.Application) -> None:
    """Действия при остановке бота"""
    logger.info("Bot shutting down...")
    
    # Удаляем webhook
    await bot.delete_webhook()
    
    # Закрываем соединение с БД
    await db_manager.disconnect()
    
    # Закрываем сессию бота
    await bot.session.close()

def main() -> None:
    """Основная функция запуска бота"""
    # Создаем приложение
    app = web.Application()
    
    # Настраиваем startup и shutdown
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    # Создаем обработчик webhook
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=config.WEBHOOK_SECRET
    )
    
    # Регистрируем webhook path
    webhook_handler.register(app, path="/webhook")
    
    # Настраиваем приложение
    setup_application(app, dp, bot=bot)
    
    # Запускаем веб-сервер
    web.run_app(
        app,
        host="0.0.0.0",
        port=config.BOT_WEBHOOK_PORT,
        handle_signals=True
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed with error: {e}")
        sys.exit(1)
