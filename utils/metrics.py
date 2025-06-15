from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Метрики
messages_total = Counter('bot_messages_total', 'Total messages processed')
errors_total = Counter('bot_errors_total', 'Total errors')
active_users = Gauge('bot_active_users', 'Currently active users')
registration_duration = Histogram('bot_registration_duration_seconds', 'Registration process duration')
database_queries = Counter('bot_database_queries_total', 'Total database queries', ['query_type'])

# Декоратор для отслеживания времени выполнения
def track_time(metric):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                metric.observe(time.time() - start_time)
        return wrapper
    return decorator

# Запуск сервера метрик
def start_metrics_server(port=9091):
    start_http_server(port)
