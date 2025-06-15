from celery import Celery
from celery.utils.log import get_task_logger
from datetime import datetime, timedelta
import asyncio
import aiohttp
from typing import Dict, Any, Optional

from config import config

# Создаем экземпляр Celery
celery = Celery('crypto_bot', broker=config.REDIS_URL)

# Конфигурация Celery
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone=config.TZ,
    enable_utc=True,
    result_expires=3600,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=250,
)

# Логгер для задач
logger = get_task_logger(__name__)

# TODO: Add Celery tasks here
