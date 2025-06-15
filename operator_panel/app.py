from flask import Flask, render_template, redirect, url_for, request, jsonify, flash, session
from werkzeug.security import check_password_hash
import asyncio
import logging
import requests
from datetime import datetime, timedelta
import re

from config import config
from database import db_manager, Operator, BotUser, Application, OperatorMessage

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создание Flask приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = config.FLASK_SECRET_KEY
app.config['SESSION_COOKIE_SECURE'] = config.SESSION_COOKIE_SECURE
app.config['SESSION_COOKIE_HTTPONLY'] = config.SESSION_COOKIE_HTTPONLY
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

def login_required(f):
    """Декоратор для проверки авторизации"""
    def wrapper(*args, **kwargs):
        if 'operator_logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/')
def index():
    """Главная страница - редирект на логин или панель"""
    if 'operator_logged_in' in session:
        return render_template('main.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    if 'operator_logged_in' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Введите логин и пароль', 'danger')
            return render_template('login.html')
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def check_login():
            async with db_manager.get_session() as db_session:
                operator = await db_session.query(Operator).filter_by(username=username).first()
                if operator and check_password_hash(operator.password_hash, password):
                    return True
                return False
        
        if loop.run_until_complete(check_login()):
            session['operator_logged_in'] = True
            session['operator_username'] = username
            session.permanent = True
            logger.info(f"Operator {username} logged in")
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль', 'danger')
            logger.warning(f"Failed login attempt for operator {username}")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Выход из системы"""
    username = session.get('operator_username', 'Unknown')
    session.clear()
    logger.info(f"Operator {username} logged out")
    return redirect(url_for('login'))

@app.route('/single')
@login_required
def send_single():
    """Страница отправки одному клиенту"""
    return render_template('send_message.html', mode='single')

@app.route('/bulk')
@login_required
def send_bulk():
    """Страница массовой рассылки"""
    return render_template('send_message.html', mode='bulk')

@app.route('/api/send', methods=['POST'])
@login_required
def api_send():
    """API endpoint для отправки сообщений"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Нет данных'}), 400
    
    mode = data.get('mode', 'single')
    message_text = data.get('message', '').strip()
    
    if not message_text:
        return jsonify({'error': 'Введите сообщение'}), 400
    
    if mode == 'single':
        # Одиночная отправка
        identifier_type = data.get('identifier_type')
        identifier = data.get('identifier', '').strip()
        
        if not identifier:
            return jsonify({'error': 'Введите идентификатор'}), 400
        
        # Определяем тип идентификатора
        if identifier.startswith('+'):
            identifier_type = 'phone'
        elif identifier.startswith('@'):
            identifier_type = 'username'
            identifier = identifier[1:]  # Убираем @
        elif identifier.isdigit():
            identifier_type = 'user_id'
        else:
            return jsonify({'error': 'Неверный формат идентификатора'}), 400
        
        # Отправляем через API бота
        response = requests.post(
            f"http://bot:{config.BOT_API_PORT}/api/send_message",
            headers={'X-API-Key': config.OPERATOR_API_KEY},
            json={
                'identifier_type': identifier_type,
                'identifier': identifier,
                'message': message_text,
                'operator_id': session.get('operator_username', 'unknown')
            }
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': 'Сообщение отправлено'
            })
        else:
            return jsonify({
                'error': 'Не удалось отправить сообщение'
            }), response.status_code
    
    else:
        # Массовая рассылка
        identifiers = data.get('identifiers', [])
        
        if not identifiers:
            return jsonify({'error': 'Нет получателей'}), 400
        
        if len(identifiers) > 1000:
            return jsonify({'error': 'Максимум 1000 получателей за раз'}), 400
        
        # Определяем тип по первому идентификатору
        first = identifiers[0].strip()
        if first.startswith('+'):
            identifier_type = 'phone'
        elif first.startswith('@'):
            identifier_type = 'username'
            identifiers = [i.strip().lstrip('@') for i in identifiers]
        elif first.isdigit():
            identifier_type = 'user_id'
        else:
            return jsonify({'error': 'Неверный формат идентификаторов'}), 400
        
        # Отправляем через API бота
        response = requests.post(
            f"http://bot:{config.BOT_API_PORT}/api/send_bulk_messages",
            headers={'X-API-Key': config.OPERATOR_API_KEY},
            json={
                'identifier_type': identifier_type,
                'identifiers': identifiers,
                'message': message_text,
                'operator_id': session.get('operator_username', 'unknown')
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                'success': True,
                'sent': result.get('sent', 0),
                'not_found': result.get('not_found', 0),
                'not_found_identifiers': result.get('not_found_identifiers', [])
            })
        else:
            return jsonify({
                'error': 'Не удалось выполнить рассылку'
            }), response.status_code

@app.route('/history')
@login_required
def history():
    """История отправок"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def get_history():
        async with db_manager.get_session() as db_session:
            # Получаем историю сообщений
            query = db_session.query(OperatorMessage).order_by(
                OperatorMessage.sent_at.desc()
            )
            
            # Фильтр по оператору
            operator_username = session.get('operator_username')
            if operator_username and operator_username != 'admin':
                query = query.filter(OperatorMessage.operator_id == operator_username)
            
            total = await query.count()
            messages = await query.offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'messages': messages,
                'total': total,
                'page': page,
                'per_page': per_page
            }
    
    data = loop.run_until_complete(get_history())
    
    return render_template('history.html', **data)

@app.template_filter('format_phone')
def format_phone(phone):
    """Форматирование телефона для отображения"""
    if not phone:
        return '-'
    # Скрываем часть номера
    if len(phone) > 7:
        return f"{phone[:4]}***{phone[-4:]}"
    return phone

@app.before_first_request
async def startup():
    """Инициализация при первом запросе"""
    await db_manager.connect()
    
    # Создаем оператора по умолчанию если его нет
    async with db_manager.get_session() as db_session:
        from werkzeug.security import generate_password_hash
        
        operator = await db_session.query(Operator).filter_by(
            username=config.OPERATOR_USERNAME
        ).first()
        
        if not operator:
            operator = Operator(
                username=config.OPERATOR_USERNAME,
                password_hash=generate_password_hash(config.OPERATOR_PASSWORD)
            )
            db_session.add(operator)
            await db_session.commit()
            logger.info("Default operator created")

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=config.OPERATOR_PANEL_PORT,
        debug=False
    )
