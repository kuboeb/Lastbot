from flask import Blueprint

# Создаем Blueprint для Facebook модуля
facebook_bp = Blueprint('facebook', __name__, 
                       template_folder='templates',
                       url_prefix='/facebook')

from . import routes
