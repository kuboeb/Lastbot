"""
Утилита для запуска асинхронного кода в синхронном Flask
"""
import asyncio
import threading
from functools import wraps

# Глобальный event loop для работы с async функциями
_loop = None
_thread = None

def get_event_loop():
    """Получить или создать event loop для работы с async"""
    global _loop, _thread
    
    if _loop is None or not _loop.is_running():
        _loop = asyncio.new_event_loop()
        _thread = threading.Thread(target=_loop.run_forever, daemon=True)
        _thread.start()
    
    return _loop

def run_async(coro):
    """Запустить асинхронную функцию в синхронном контексте"""
    loop = get_event_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=30)

def async_to_sync(func):
    """Декоратор для преобразования async функции в sync"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return run_async(func(*args, **kwargs))
    return wrapper
