import os
import sys
from datetime import datetime, timedelta
from functools import wraps
import asyncio

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import select, func, and_, or_

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from database import db_manager, Operator, BotUser, Application

app = Flask(__name__)
app.config['SECRET_KEY'] = config.FLASK_SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    operator = asyncio.run(get_operator_by_id(int(user_id)))
    if operator:
        return User(operator.id, operator.username)
    return None

async def get_operator_by_id(operator_id):
    async with db_manager.get_session() as session:
        result = await session.execute(
            select(Operator).where(Operator.id == operator_id)
        )
        return result.scalar_one_or_none()

async def get_operator_by_username(username):
    async with db_manager.get_session() as session:
        result = await session.execute(
            select(Operator).where(Operator.username == username)
        )
        return result.scalar_one_or_none()

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        operator = asyncio.run(get_operator_by_username(username))
        
        if operator and check_password_hash(operator.password_hash, password):
            user = User(operator.id, operator.username)
            login_user(user, remember=True)
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/index')
@login_required
def index():
    return render_template('index.html')

@app.route('/single')
@login_required
def single_message():
    return render_template('send_message.html')

@app.route('/bulk')
@login_required
def bulk_message():
    return render_template('bulk_message.html')

@app.route('/history')
@login_required
def history():
    # Здесь будет логика получения истории
    messages = []
    return render_template('history.html', messages=messages)

# API endpoints для отправки сообщений
@app.route('/api/send_single', methods=['POST'])
@login_required
async def send_single():
    data = request.json
    identifier_type = data.get('identifier_type')
    identifier = data.get('identifier')
    message = data.get('message')
    
    # Здесь будет логика отправки через API бота
    # Пока возвращаем заглушку
    return jsonify({
        'status': 'success',
        'message': 'Сообщение отправлено'
    })

@app.route('/api/send_bulk', methods=['POST'])
@login_required
async def send_bulk():
    data = request.json
    identifier_type = data.get('identifier_type')
    identifiers = data.get('identifiers', [])
    message = data.get('message')
    
    # Здесь будет логика массовой отправки
    return jsonify({
        'status': 'success',
        'sent': len(identifiers),
        'not_found': 0
    })

# Инициализация базы данных
async def init_database():
    await db_manager.connect()
    async with db_manager.get_session() as session:
        # Проверяем, есть ли оператор
        result = await session.execute(
            select(Operator).where(Operator.username == config.OPERATOR_USERNAME)
        )
        operator = result.scalar_one_or_none()
        
        if not operator:
            # Создаем оператора по умолчанию
            operator = Operator(
                username=config.OPERATOR_USERNAME,
                password_hash=generate_password_hash(config.OPERATOR_PASSWORD)
            )
            session.add(operator)
            await session.commit()
            print(f"Created default operator: {config.OPERATOR_USERNAME}")

if __name__ == '__main__':
    # Инициализируем базу данных перед запуском
    asyncio.run(init_database())
    
    app.run(
        host='0.0.0.0',
        port=config.OPERATOR_PANEL_PORT,
        debug=False
    )
