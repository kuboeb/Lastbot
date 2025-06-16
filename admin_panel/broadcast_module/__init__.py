from flask import Blueprint

# Создаем Blueprint для модуля рассылок
broadcast_bp = Blueprint(
    'broadcast',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/broadcast'
)

from . import routes
