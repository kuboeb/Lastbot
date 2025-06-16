# Добавьте эти строки в app.py после импортов:

# Импорт модуля рассылок
from broadcast_module import broadcast_bp
from broadcast_module.routes import init_broadcast_module

# После создания app добавьте:
# Инициализация модуля рассылок
init_broadcast_module(app, get_db_connection, None)  # bot_instance передадим позже
app.register_blueprint(broadcast_bp)

# Удалите или закомментируйте старые роуты broadcast если они есть
