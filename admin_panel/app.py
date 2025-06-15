import os
import sys
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import asyncio
from sqlalchemy import select, func, and_, or_

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

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    admin = asyncio.run(get_admin_by_id(int(user_id)))
    if admin:
        return User(admin.id, admin.username)
    return None

async def get_admin_by_id(admin_id):
    async with db_manager.session() as session:
        result = await session.execute(
            select(Admin).where(Admin.id == admin_id)
        )
        return result.scalar_one_or_none()

async def get_admin_by_username(username):
    async with db_manager.session() as session:
        result = await session.execute(
            select(Admin).where(Admin.username == username)
        )
        return result.scalar_one_or_none()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = asyncio.run(get_admin_by_username(username))
        
        if admin and check_password_hash(admin.password_hash, password):
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
async def dashboard():
    async with db_manager.session() as session:
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
        
        # Статус бота
        bot_status = {'enabled': True, 'uptime': '2д 14ч 35м'}
        
        return render_template('dashboard.html',
                             today_count=today_count,
                             week_count=week_count,
                             month_count=month_count,
                             recent_applications=recent_applications,
                             bot_status=bot_status)

@app.route('/applications')
@login_required
async def applications():
    async with db_manager.session() as session:
        apps = await session.execute(
            select(Application).order_by(Application.created_at.desc())
        )
        applications_list = apps.scalars().all()
        return render_template('applications.html', applications=applications_list)

@app.route('/users')
@login_required
async def users():
    async with db_manager.session() as session:
        users = await session.execute(
            select(BotUser).order_by(BotUser.first_seen.desc())
        )
        users_list = users.scalars().all()
        return render_template('users.html', users=users_list)

@app.route('/editor')
@login_required
async def editor():
    async with db_manager.session() as session:
        texts = await session.execute(
            select(BotText).order_by(BotText.category, BotText.key)
        )
        texts_list = texts.scalars().all()
        return render_template('editor.html', texts=texts_list)

@app.route('/broadcast')
@login_required
def broadcast():
    return render_template('broadcast.html')

@app.route('/traffic-sources')
@login_required
async def traffic_sources():
    async with db_manager.session() as session:
        sources = await session.execute(
            select(TrafficSource).order_by(TrafficSource.created_at.desc())
        )
        sources_list = sources.scalars().all()
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
async def funnel_stats():
    async with db_manager.session() as session:
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
async def init_database():
    await db_manager.connect()
    async with db_manager.session() as session:
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

if __name__ == '__main__':
    # Инициализируем базу данных перед запуском
    asyncio.run(init_database())
    
    app.run(
        host='0.0.0.0',
        port=config.ADMIN_PANEL_PORT,
        debug=False
    )
