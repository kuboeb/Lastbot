import os
import sys
from datetime import datetime, timedelta
from functools import wraps
import asyncio
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import select, func, and_, or_
import nest_asyncio

# Применяем nest_asyncio для совместимости event loops
nest_asyncio.apply()

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from database import db_manager, Admin, Application, BotUser, TrafficSource, BotText

app = Flask(__name__)
app.config['SECRET_KEY'] = config.FLASK_SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Создаем executor для запуска асинхронного кода
executor = ThreadPoolExecutor(max_workers=10)

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

def run_async(coro):
    """Запускает асинхронную функцию в синхронном контексте"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@login_manager.user_loader
def load_user(user_id):
    admin = run_async(get_admin_by_id(int(user_id)))
    if admin:
        return User(admin.id, admin.username)
    return None

async def get_admin_by_id(admin_id):
    async with db_manager.get_session() as session:
        result = await session.execute(
            select(Admin).where(Admin.id == admin_id)
        )
        return result.scalar_one_or_none()

async def get_admin_by_username(username):
    async with db_manager.get_session() as session:
        result = await session.execute(
            select(Admin).where(Admin.username == username)
        )
        return result.scalar_one_or_none()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = run_async(get_admin_by_username(username))
        
        if admin and admin.password_hash and check_password_hash(admin.password_hash, password):
            user = User(admin.id, admin.username)
            login_user(user, remember=True)
            return redirect(url_for('dashboard'))
        else:
            flash('Неверный логин или пароль', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    async def get_dashboard_data():
        async with db_manager.get_session() as session:
            # Получаем статистику
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            # Заявки за сегодня
            today_apps = await session.execute(
                select(func.count(Application.id)).where(
                    func.date(Application.created_at) == today
                )
            )
            today_count = today_apps.scalar() or 0
            
            # Заявки за неделю
            week_apps = await session.execute(
                select(func.count(Application.id)).where(
                    Application.created_at >= week_ago
                )
            )
            week_count = week_apps.scalar() or 0
            
            # Заявки за месяц
            month_apps = await session.execute(
                select(func.count(Application.id)).where(
                    Application.created_at >= month_ago
                )
            )
            month_count = month_apps.scalar() or 0
            
            # Последние 10 заявок
            recent_apps = await session.execute(
                select(Application).order_by(Application.created_at.desc()).limit(10)
            )
            recent_applications = recent_apps.scalars().all()
            
            return {
                'today_count': today_count,
                'week_count': week_count,
                'month_count': month_count,
                'recent_applications': recent_applications
            }
    
    data = run_async(get_dashboard_data())
    data['bot_status'] = {'enabled': True, 'uptime': '2д 14ч 35м'}
    
    return render_template('dashboard.html', **data)

@app.route('/applications')
@login_required
def applications():
    async def get_applications():
        async with db_manager.get_session() as session:
            apps = await session.execute(
                select(Application).order_by(Application.created_at.desc())
            )
            return apps.scalars().all()
    
    applications_list = run_async(get_applications())
    return render_template('applications.html', applications=applications_list)

@app.route('/users')
@login_required
def users():
    async def get_users():
        async with db_manager.get_session() as session:
            users = await session.execute(
                select(BotUser).order_by(BotUser.first_seen.desc())
            )
            return users.scalars().all()
    
    users_list = run_async(get_users())
    return render_template('users.html', users=users_list)

@app.route('/editor')
@login_required
def editor():
    async def get_texts():
        async with db_manager.get_session() as session:
            texts = await session.execute(
                select(BotText).order_by(BotText.category, BotText.key)
            )
            return texts.scalars().all()
    
    texts_list = run_async(get_texts())
    return render_template('editor.html', texts=texts_list)

@app.route('/broadcast')
@login_required
def broadcast():
    return render_template('broadcast.html')

@app.route('/traffic-sources')
@login_required
def traffic_sources():
    async def get_sources():
        async with db_manager.get_session() as session:
            sources = await session.execute(
                select(TrafficSource).order_by(TrafficSource.created_at.desc())
            )
            return sources.scalars().all()
    
    sources_list = run_async(get_sources())
    return render_template('traffic_sources.html', sources=sources_list)

@app.route('/system')
@login_required
def system():
    return render_template('system.html')

# API endpoints
@app.route('/api/bot/toggle', methods=['POST'])
@login_required
def toggle_bot():
    # Здесь логика включения/выключения бота
    return jsonify({'status': 'success', 'enabled': True})

@app.route('/api/stats/funnel')
@login_required
def funnel_stats():
    # Здесь логика получения статистики воронки
    stats = {
        'started': 1000,
        'entered_name': 800,
        'entered_country': 700,
        'entered_phone': 650,
        'entered_time': 600,
        'completed': 580
    }
    return jsonify(stats)

# Инициализация базы данных при запуске
def init_database():
    """Инициализирует базу данных и создает админа по умолчанию"""
    async def _init():
        await db_manager.connect()
        async with db_manager.get_session() as session:
            # Проверяем, есть ли админ
            result = await session.execute(
                select(Admin).where(Admin.username == config.ADMIN_USERNAME)
            )
            admin = result.scalar_one_or_none()
            
            if not admin:
                # Создаем админа по умолчанию
                admin = Admin(
                    username=config.ADMIN_USERNAME,
                    password_hash=generate_password_hash(config.ADMIN_PASSWORD)
                )
                session.add(admin)
                await session.commit()
                print(f"Created default admin: {config.ADMIN_USERNAME}")
    
    run_async(_init())

if __name__ == '__main__':
    # Инициализируем базу данных перед запуском
    init_database()
    
    app.run(
        host='0.0.0.0',
        port=config.ADMIN_PANEL_PORT,
        debug=False
    )
