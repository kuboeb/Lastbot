from flask import Blueprint

# Создаем Blueprint для модуля рассылок
mailing_bp = Blueprint(
    'mailing',
    __name__,
    template_folder='templates',
    url_prefix='/mailing'
)

# Импортируем routes после создания Blueprint
from . import routes
