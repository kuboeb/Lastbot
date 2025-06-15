"""
Админ-панель для управления ботом (синхронная версия)
"""
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Подключение к БД
def get_db_connection():
    """Получить синхронное подключение к БД"""
    return psycopg2.connect(
        host='localhost',
        database='crypto_course_db',
        user='cryptobot',
        password='kuboeb1A',
        cursor_factory=RealDictCursor
    )

class Admin:
    def __init__(self, id, username):
        self.id = id
        self.username = username
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
    
    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username FROM admins WHERE id = %s", (int(user_id),))
    admin_data = cur.fetchone()
    cur.close()
    conn.close()
    
    if admin_data:
        return Admin(admin_data['id'], admin_data['username'])
    return None

@app.route('/')
@app.route('/admin')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, password_hash FROM admins WHERE username = %s", (username,))
        admin_data = cur.fetchone()
        cur.close()
        conn.close()
        
        if admin_data and check_password_hash(admin_data['password_hash'], password):
            admin = Admin(admin_data['id'], admin_data['username'])
            login_user(admin)
            return redirect(url_for('dashboard'))
        else:
            flash('Неверный логин или пароль', 'error')
    
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Статистика за сегодня
    today = datetime.now().date()
    cur.execute("""
        SELECT COUNT(*) as count FROM applications 
        WHERE DATE(created_at) = %s
    """, (today,))
    today_count = cur.fetchone()['count']
    
    # Статистика за неделю
    week_ago = today - timedelta(days=7)
    cur.execute("""
        SELECT COUNT(*) as count FROM applications 
        WHERE created_at >= %s
    """, (week_ago,))
    week_count = cur.fetchone()['count']
    
    # Статистика за месяц
    month_ago = today - timedelta(days=30)
    cur.execute("""
        SELECT COUNT(*) as count FROM applications 
        WHERE created_at >= %s
    """, (month_ago,))
    month_count = cur.fetchone()['count']
    
    # Последние 10 заявок
    cur.execute("""
        SELECT * FROM applications 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    recent_applications = cur.fetchall()
    
    # Конверсия
    cur.execute("SELECT COUNT(*) as count FROM bot_users WHERE first_seen >= %s", (week_ago,))
    total_users = cur.fetchone()['count']
    conversion_rate = (week_count / total_users * 100) if total_users > 0 else 0
    
    # Данные для графика
    chart_labels = []
    chart_data = []
    for i in range(7):
        date = today - timedelta(days=6-i)
        chart_labels.append(date.strftime('%d.%m'))
        cur.execute("""
            SELECT COUNT(*) as count FROM applications 
            WHERE DATE(created_at) = %s
        """, (date,))
        chart_data.append(cur.fetchone()['count'])
    
    cur.close()
    conn.close()
    
    return render_template('dashboard.html',
        today_count=today_count,
        week_count=week_count,
        month_count=month_count,
        recent_applications=recent_applications,
        conversion_rate=conversion_rate,
        chart_labels=chart_labels,
        chart_data=chart_data,
        bot_status={'enabled': True, 'uptime': '2д 14ч 35м'}
    )

@app.route('/applications')
@login_required
def applications():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.*, 
               CASE 
                   WHEN a.referrer_id IS NOT NULL THEN 'Реферал'
                   WHEN a.source_id IS NOT NULL THEN 'Баер'
                   ELSE 'Прямой'
               END as source_type
        FROM applications a
        ORDER BY created_at DESC
    """)
    applications = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('applications.html', applications=applications)

@app.route('/users')
@login_required
def users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.*, 
               COUNT(DISTINCT a.id) as has_application,
               COUNT(DISTINCT r.referred_id) as referrals_count
        FROM bot_users u
        LEFT JOIN applications a ON u.user_id = a.user_id
        LEFT JOIN referrals r ON u.user_id = r.referrer_id
        GROUP BY u.id, u.user_id, u.username, u.first_seen, u.last_activity, u.source_id, u.has_application, u.is_blocked
        ORDER BY u.first_seen DESC
    """)
    users = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('users.html', users=users)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Создадим начального админа если его нет
def init_admin():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM admins WHERE username = 'admin'")
    if not cur.fetchone():
        password_hash = generate_password_hash('kuboeb1A')
        cur.execute(
            "INSERT INTO admins (username, password_hash) VALUES (%s, %s)",
            ('admin', password_hash)
        )
        conn.commit()
        print("Admin user created")
    cur.close()
    conn.close()

if __name__ == '__main__':
    init_admin()
    app.run(host='0.0.0.0', port=8000, debug=False)

@app.route('/editor')
@login_required
def text_editor():
    return "<h1>Редактор текстов (в разработке)</h1><a href='/dashboard'>Назад</a>"

@app.route('/broadcast')
@login_required
def broadcast():
    return "<h1>Рассылка (в разработке)</h1><a href='/dashboard'>Назад</a>"

@app.route('/traffic-sources')
@login_required
def traffic_sources():
    return "<h1>Источники трафика (в разработке)</h1><a href='/dashboard'>Назад</a>"

@app.route('/system')
@login_required
def system():
    return "<h1>Информация о системе (в разработке)</h1><a href='/dashboard'>Назад</a>"
