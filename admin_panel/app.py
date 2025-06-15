from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import asyncio
import logging
from datetime import datetime, timedelta
import json

from config import config
from database import db_manager, Admin, Application, BotUser, TrafficSource, BotText
from admin_panel.forms import LoginForm, ApplicationFilterForm, TextEditForm
from admin_panel.models import AdminUser

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
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице'

@login_manager.user_loader
def load_user(user_id):
    """Загрузка пользователя для Flask-Login"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def get_admin():
        async with db_manager.get_session() as session:
            admin = await session.get(Admin, int(user_id))
            if admin:
                return AdminUser(admin.id, admin.username)
            return None
    
    return loop.run_until_complete(get_admin())

@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def check_login():
            async with db_manager.get_session() as session:
                admin = await session.query(Admin).filter_by(username=username).first()
                if admin and check_password_hash(admin.password_hash, password):
                    return AdminUser(admin.id, admin.username)
                return None
        
        user = loop.run_until_complete(check_login())
        
        if user:
            login_user(user, remember=True)
            logger.info(f"Admin {username} logged in")
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Неверный логин или пароль', 'danger')
            logger.warning(f"Failed login attempt for {username}")
    
    return render_template('login.html', form=form)

@app.route('/admin/logout')
@login_required
def logout():
    """Выход из системы"""
    logger.info(f"Admin {current_user.username} logged out")
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin')
@app.route('/admin/dashboard')
@login_required
def dashboard():
    """Главная страница - дашборд с воронкой"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def get_stats():
        async with db_manager.get_session() as session:
            from sqlalchemy import func, and_
            from database import UserAction, Referral
            
            # Статистика за сегодня
            today = datetime.now().date()
            
            # Новые заявки
            new_apps_today = await session.query(func.count(Application.id)).filter(
                func.date(Application.created_at) == today
            ).scalar()
            
            # Новые рефералы
            new_referrals_today = await session.query(func.count(Referral.id)).filter(
                func.date(Referral.created_at) == today
            ).scalar()
            
            # Воронка регистрации
            funnel_stats = {}
            actions = ['start', 'begin_registration', 'enter_name', 'enter_country', 
                      'enter_phone', 'enter_time', 'complete_registration']
            
            for action in actions:
                count = await session.query(func.count(func.distinct(UserAction.user_id))).filter(
                    UserAction.action == action,
                    func.date(UserAction.created_at) >= today - timedelta(days=7)
                ).scalar()
                funnel_stats[action] = count
            
            # Последние заявки
            recent_apps = await session.query(Application).order_by(
                Application.created_at.desc()
            ).limit(10).all()
            
            return {
                'new_apps_today': new_apps_today,
                'new_referrals_today': new_referrals_today,
                'funnel_stats': funnel_stats,
                'recent_apps': recent_apps
            }
    
    stats = loop.run_until_complete(get_stats())
    
    return render_template('dashboard.html', **stats)

@app.route('/admin/applications')
@login_required
def applications():
    """Страница заявок"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def get_applications():
        async with db_manager.get_session() as session:
            # Базовый запрос
            query = session.query(Application).order_by(Application.created_at.desc())
            
            # Фильтры
            date_from = request.args.get('date_from')
            date_to = request.args.get('date_to')
            country = request.args.get('country')
            source = request.args.get('source')
            
            if date_from:
                query = query.filter(Application.created_at >= date_from)
            if date_to:
                query = query.filter(Application.created_at <= date_to)
            if country:
                query = query.filter(Application.country.ilike(f'%{country}%'))
            if source:
                query = query.filter(Application.source_id == source)
            
            # Пагинация
            total = await query.count()
            apps = await query.offset((page - 1) * per_page).limit(per_page).all()
            
            # Получаем список стран для фильтра
            countries = await session.query(
                Application.country, func.count(Application.id)
            ).group_by(Application.country).all()
            
            # Получаем источники
            sources = await session.query(TrafficSource).filter_by(is_active=True).all()
            
            return {
                'applications': apps,
                'total': total,
                'page': page,
                'per_page': per_page,
                'countries': countries,
                'sources': sources
            }
    
    data = loop.run_until_complete(get_applications())
    
    return render_template('applications.html', **data)

@app.route('/admin/users')
@login_required
def users():
    """Страница пользователей"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def get_users():
        async with db_manager.get_session() as session:
            query = session.query(BotUser).order_by(BotUser.last_activity.desc())
            
            # Фильтры
            has_application = request.args.get('has_application')
            if has_application == 'yes':
                query = query.filter(BotUser.has_application == True)
            elif has_application == 'no':
                query = query.filter(BotUser.has_application == False)
            
            total = await query.count()
            users = await query.offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'users': users,
                'total': total,
                'page': page,
                'per_page': per_page
            }
    
    data = loop.run_until_complete(get_users())
    
    return render_template('users.html', **data)

@app.route('/admin/editor')
@login_required
def text_editor():
    """Редактор текстов бота"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def get_texts():
        async with db_manager.get_session() as session:
            texts = await session.query(BotText).order_by(
                BotText.category, BotText.key
            ).all()
            
            # Группируем по категориям
            categories = {}
            for text in texts:
                if text.category not in categories:
                    categories[text.category] = []
                categories[text.category].append(text)
            
            return categories
    
    categories = loop.run_until_complete(get_texts())
    
    return render_template('text_editor.html', categories=categories)

@app.route('/admin/traffic-sources')
@login_required
def traffic_sources():
    """Управление источниками трафика"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def get_sources():
        async with db_manager.get_session() as session:
            sources = await session.query(TrafficSource).all()
            
            # Добавляем статистику для каждого источника
            for source in sources:
                # Считаем клики и конверсии
                from database import TrackingEvent
                clicks = await session.query(func.count(TrackingEvent.id)).filter(
                    TrackingEvent.source_id == source.id,
                    TrackingEvent.event_type == 'click'
                ).scalar()
                
                leads = await session.query(func.count(Application.id)).filter(
                    Application.source_id == source.id
                ).scalar()
                
                source.clicks = clicks
                source.leads = leads
                source.cr = round(leads / clicks * 100, 2) if clicks > 0 else 0
            
            return sources
    
    sources = loop.run_until_complete(get_sources())
    
    return render_template('traffic_sources.html', sources=sources)

# API endpoints для AJAX запросов
@app.route('/admin/api/bot/toggle', methods=['POST'])
@login_required
def toggle_bot():
    """Включение/выключение бота"""
    import requests
    
    response = requests.post(
        f"http://localhost:{config.BOT_API_PORT}/api/bot/toggle",
        headers={'X-API-Key': config.INTERNAL_API_KEY}
    )
    
    return jsonify(response.json())

@app.route('/admin/api/stats/chart')
@login_required
def stats_chart():
    """Данные для графика на дашборде"""
    days = request.args.get('days', 7, type=int)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def get_chart_data():
        async with db_manager.get_session() as session:
            data = []
            
            for i in range(days):
                date = datetime.now().date() - timedelta(days=i)
                
                count = await session.query(func.count(Application.id)).filter(
                    func.date(Application.created_at) == date
                ).scalar()
                
                data.append({
                    'date': date.strftime('%d.%m'),
                    'count': count
                })
            
            return list(reversed(data))
    
    chart_data = loop.run_until_complete(get_chart_data())
    
    return jsonify(chart_data)

    await db_manager.connect()
    
    # Создаем админа по умолчанию если его нет
    async with db_manager.get_session() as session:
        admin = await session.query(Admin).filter_by(username=config.ADMIN_USERNAME).first()
        if not admin:
            admin = Admin(
                username=config.ADMIN_USERNAME,
                password_hash=generate_password_hash(config.ADMIN_PASSWORD)
            )
            session.add(admin)
            await session.commit()
            logger.info("Default admin created")

# Initialize database on startup
with app.app_context():
    from database import db_manager
    import asyncio
    asyncio.run(db_manager.connect())

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=config.ADMIN_PANEL_PORT,
        debug=False
    )

