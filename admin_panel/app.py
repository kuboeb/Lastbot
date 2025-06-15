"""
Админ-панель для управления ботом
"""
from flask import Flask, render_template, request

def format_datetime(dt):
    '''Форматировать datetime для отображения'''
    if dt and hasattr(dt, 'astimezone'):
        return dt.astimezone(TIMEZONE).strftime('%d.%m.%Y %H:%M')
    return '-', redirect, url_for, request, flash, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import pytz
import os
import io
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

# Временная зона GMT+3 (Москва)
TIMEZONE = pytz.timezone('Europe/Moscow')

def get_local_time():
    '''Получить текущее время в GMT+3'''
    return datetime.now(TIMEZONE)

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@app.template_filter('datetime')
def datetime_filter(dt):
    return format_datetime(dt)

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
    today = get_local_time().date()
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
    
    # Получаем данные воронки
    funnel_stats = {}
    
    # Начали регистрацию
    cur.execute("""
        SELECT COUNT(DISTINCT user_id) as count FROM user_actions 
        WHERE action = 'begin_registration' AND created_at >= %s
    """, (week_ago,))
    result = cur.fetchone()
    funnel_stats['start'] = result['count'] if result else 0
    
    # Ввели имя
    cur.execute("""
        SELECT COUNT(DISTINCT user_id) as count FROM user_actions 
        WHERE action = 'enter_name' AND created_at >= %s
    """, (week_ago,))
    result = cur.fetchone()
    funnel_stats['begin_registration'] = result['count'] if result else 0
    
    # Ввели страну
    cur.execute("""
        SELECT COUNT(DISTINCT user_id) as count FROM user_actions 
        WHERE action = 'enter_country' AND created_at >= %s
    """, (week_ago,))
    result = cur.fetchone()
    funnel_stats['entered_country'] = result['count'] if result else 0
    
    # Ввели телефон
    cur.execute("""
        SELECT COUNT(DISTINCT user_id) as count FROM user_actions 
        WHERE action = 'enter_phone' AND created_at >= %s
    """, (week_ago,))
    result = cur.fetchone()
    funnel_stats['entered_phone'] = result['count'] if result else 0
    
    # Выбрали время
    cur.execute("""
        SELECT COUNT(DISTINCT user_id) as count FROM user_actions 
        WHERE action = 'enter_time' AND created_at >= %s
    """, (week_ago,))
    result = cur.fetchone()
    funnel_stats['entered_time'] = result['count'] if result else 0
    
    # Завершили регистрацию
    cur.execute("""
        SELECT COUNT(DISTINCT user_id) as count FROM user_actions 
        WHERE action = 'completed' AND created_at >= %s
    """, (week_ago,))
    result = cur.fetchone()
    funnel_stats['complete_registration'] = result['count'] if result else 0
    
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
        bot_status={'enabled': True, 'uptime': '2д 14ч 35м'},
        funnel_stats=funnel_stats
    )

@app.route('/applications')
@login_required
def applications():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Параметры
    page = request.args.get('page', 1, type=int)
    per_page = 50
    search = request.args.get('search', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    country = request.args.get('country', '')
    source_type = request.args.get('source_type', '')
    preferred_time = request.args.get('preferred_time', '')
    
    # Базовый запрос
    base_query = """
        FROM applications a
        LEFT JOIN bot_users u ON a.user_id = u.user_id
        WHERE 1=1
    """
    params = []
    
    # Фильтры
    if search:
        base_query += " AND (LOWER(a.full_name) LIKE LOWER(%s) OR a.phone LIKE %s)"
        params.extend([f'%{search}%', f'%{search}%'])
    
    if date_from:
        base_query += " AND a.created_at >= %s"
        params.append(date_from)
    
    if date_to:
        base_query += " AND a.created_at <= %s"
        params.append(date_to + ' 23:59:59')
    
    if country:
        base_query += " AND LOWER(a.country) LIKE LOWER(%s)"
        params.append(f'%{country}%')
    
    if source_type:
        if source_type == 'direct':
            base_query += " AND a.referrer_id IS NULL AND a.source_id IS NULL"
        elif source_type == 'referral':
            base_query += " AND a.referrer_id IS NOT NULL"
        elif source_type == 'source':
            base_query += " AND a.source_id IS NOT NULL"
    
    if preferred_time:
        base_query += " AND a.preferred_time = %s"
        params.append(preferred_time)
    
    # Подсчет общего количества
    count_query = "SELECT COUNT(*) as total " + base_query
    cur.execute(count_query, params)
    total_count = cur.fetchone()['total']
    total_pages = (total_count + per_page - 1) // per_page
    
    # Получение данных с пагинацией
    offset = (page - 1) * per_page
    data_query = """
        SELECT a.*, 
               u.username,
               CASE 
                   WHEN a.referrer_id IS NOT NULL THEN 'Реферал'
                   WHEN a.source_id IS NOT NULL THEN 'Источник ' || a.source_id
                   ELSE 'Прямой'
               END as source_type,
               CASE 
                   WHEN a.referrer_id IS NOT NULL THEN 
                       (SELECT username FROM bot_users WHERE user_id = a.referrer_id LIMIT 1)
                   ELSE NULL
               END as referrer_username,
               EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - a.created_at))/3600 as hours_ago
    """ + base_query + " ORDER BY a.created_at DESC LIMIT %s OFFSET %s"
    params.extend([per_page, offset])
    
    cur.execute(data_query, params)
    applications = cur.fetchall()
    
    # Статистика
    today = get_local_time().date()
    cur.execute("SELECT COUNT(*) as count FROM applications WHERE DATE(created_at) = %s", (today,))
    today_count = cur.fetchone()['count']
    
    week_ago = today - timedelta(days=7)
    cur.execute("SELECT COUNT(*) as count FROM applications WHERE created_at >= %s", (week_ago,))
    week_applications = cur.fetchone()['count']
    cur.execute("SELECT COUNT(*) as count FROM bot_users WHERE first_seen >= %s", (week_ago,))
    week_users = cur.fetchone()['count']
    conversion_rate = (week_applications / week_users * 100) if week_users > 0 else 0
    
    # Список стран
    cur.execute("SELECT DISTINCT country FROM applications WHERE country IS NOT NULL ORDER BY country")
    countries = [row['country'] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return render_template('applications.html', 
                         applications=applications,
                         page=page,
                         total_pages=total_pages,
                         total_count=total_count,
                         per_page=per_page,
                         today_count=today_count,
                         conversion_rate=conversion_rate,
                         countries=countries)

@app.route('/export_applications')
@login_required
def export_applications():
    import xlsxwriter
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Те же фильтры что и в applications()
    search = request.args.get('search', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    country = request.args.get('country', '')
    source_type = request.args.get('source_type', '')
    preferred_time = request.args.get('preferred_time', '')
    
    query = """
        SELECT a.*, 
               u.username,
               CASE 
                   WHEN a.referrer_id IS NOT NULL THEN 'Реферал'
                   WHEN a.source_id IS NOT NULL THEN 'Источник ' || a.source_id
                   ELSE 'Прямой'
               END as source_type
        FROM applications a
        LEFT JOIN bot_users u ON a.user_id = u.user_id
        WHERE 1=1
    """
    params = []
    
    if search:
        query += " AND (LOWER(a.full_name) LIKE LOWER(%s) OR a.phone LIKE %s)"
        params.extend([f'%{search}%', f'%{search}%'])
    
    if date_from:
        query += " AND a.created_at >= %s"
        params.append(date_from)
    
    if date_to:
        query += " AND a.created_at <= %s"
        params.append(date_to + ' 23:59:59')
    
    if country:
        query += " AND LOWER(a.country) LIKE LOWER(%s)"
        params.append(f'%{country}%')
    
    if source_type:
        if source_type == 'direct':
            query += " AND a.referrer_id IS NULL AND a.source_id IS NULL"
        elif source_type == 'referral':
            query += " AND a.referrer_id IS NOT NULL"
        elif source_type == 'source':
            query += " AND a.source_id IS NOT NULL"
    
    if preferred_time:
        query += " AND a.preferred_time = %s"
        params.append(preferred_time)
    
    query += " ORDER BY a.created_at DESC"
    
    cur.execute(query, params)
    applications = cur.fetchall()
    cur.close()
    conn.close()
    
    # Создаем Excel
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('Заявки')
    
    # Заголовки
    headers = ['ID', 'Имя', 'Страна', 'Телефон', 'Время звонка', 'Дата создания', 'Источник', 'Username']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)
    
    # Данные
    for row, app in enumerate(applications, 1):
        worksheet.write(row, 0, app['id'])
        worksheet.write(row, 1, app['full_name'])
        worksheet.write(row, 2, app['country'])
        worksheet.write(row, 3, app['phone'])
        worksheet.write(row, 4, app['preferred_time'])
        worksheet.write(row, 5, format_datetime(app['created_at']))
        worksheet.write(row, 6, app['source_type'])
        worksheet.write(row, 7, f"@{app['username']}" if app['username'] else '-')
    
    workbook.close()
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'applications_{get_local_time().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )

@app.route('/users')
@login_required
def users():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Параметры
    page = request.args.get('page', 1, type=int)
    per_page = 50
    search = request.args.get('search', '')
    has_application = request.args.get('has_application', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Базовый запрос
    base_query = """
        FROM bot_users u
        LEFT JOIN applications a ON u.user_id = a.user_id
        LEFT JOIN referrals r ON u.user_id = r.referrer_id
        WHERE 1=1
    """
    params = []
    
    # Фильтры
    if search:
        base_query += " AND (u.username ILIKE %s OR CAST(u.user_id AS TEXT) LIKE %s)"
        params.extend([f'%{search}%', f'%{search}%'])
    
    if date_from:
        base_query += " AND u.first_seen >= %s"
        params.append(date_from)
    
    if date_to:
        base_query += " AND u.first_seen <= %s"
        params.append(date_to + ' 23:59:59')
    
    # Группировка для подсчета
    group_by = " GROUP BY u.id, u.user_id, u.username, u.first_seen, u.last_activity, u.source_id, u.has_application, u.is_blocked"
    
    # Фильтр по наличию заявки
    having_clause = ""
    if has_application == '1':
        having_clause = " HAVING COUNT(DISTINCT a.id) > 0"
    elif has_application == '0':
        having_clause = " HAVING COUNT(DISTINCT a.id) = 0"
    
    # Подсчет общего количества
    count_query = "SELECT COUNT(*) as total FROM (SELECT u.id " + base_query + group_by + having_clause + ") as subquery"
    cur.execute(count_query, params)
    total_count = cur.fetchone()['total']
    total_pages = (total_count + per_page - 1) // per_page
    
    # Получение данных с пагинацией
    offset = (page - 1) * per_page
    data_query = """
        SELECT u.*, 
               COUNT(DISTINCT a.id) as has_application,
               COUNT(DISTINCT r.referred_id) as referrals_count
    """ + base_query + group_by + having_clause + " ORDER BY u.first_seen DESC LIMIT %s OFFSET %s"
    params.extend([per_page, offset])
    
    cur.execute(data_query, params)
    users = cur.fetchall()
    
    # Общее количество всех пользователей
    cur.execute("SELECT COUNT(*) as count FROM bot_users")
    all_users_count = cur.fetchone()['count']
    
    cur.close()
    conn.close()
    
    return render_template('users.html', 
                         users=users,
                         page=page,
                         total_pages=total_pages,
                         total_count=total_count,
                         all_users_count=all_users_count,
                         per_page=per_page)

@app.route('/export_users')
@login_required
def export_users():
    import xlsxwriter
    
    # Получаем те же данные с фильтрами
    conn = get_db_connection()
    cur = conn.cursor()
    
    search = request.args.get('search', '')
    has_application = request.args.get('has_application', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = """
        SELECT u.*, 
               COUNT(DISTINCT a.id) as has_application,
               COUNT(DISTINCT r.referred_id) as referrals_count
        FROM bot_users u
        LEFT JOIN applications a ON u.user_id = a.user_id
        LEFT JOIN referrals r ON u.user_id = r.referrer_id
        WHERE 1=1
    """
    params = []
    
    if search:
        query += " AND (u.username ILIKE %s OR CAST(u.user_id AS TEXT) LIKE %s)"
        params.extend([f'%{search}%', f'%{search}%'])
    
    if date_from:
        query += " AND u.first_seen >= %s"
        params.append(date_from)
    
    if date_to:
        query += " AND u.first_seen <= %s"
        params.append(date_to + ' 23:59:59')
    
    query += " GROUP BY u.id, u.user_id, u.username, u.first_seen, u.last_activity, u.source_id, u.has_application, u.is_blocked"
    
    if has_application == '1':
        query += " HAVING COUNT(DISTINCT a.id) > 0"
    elif has_application == '0':
        query += " HAVING COUNT(DISTINCT a.id) = 0"
    
    query += " ORDER BY u.first_seen DESC"
    
    cur.execute(query, params)
    users = cur.fetchall()
    cur.close()
    conn.close()
    
    # Создаем Excel файл в памяти
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('Пользователи')
    
    # Заголовки
    headers = ['ID', 'User ID', 'Username', 'Первый вход', 'Последняя активность', 
               'Есть заявка', 'Рефералов', 'Источник']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)
    
    # Данные
    for row, user in enumerate(users, 1):
        worksheet.write(row, 0, user['id'])
        worksheet.write(row, 1, str(user['user_id']))
        worksheet.write(row, 2, user['username'] or '-')
        worksheet.write(row, 3, user['first_seen'].strftime('%d.%m.%Y %H:%M') if user['first_seen'] else '-')
        worksheet.write(row, 4, user['last_activity'].strftime('%d.%m.%Y %H:%M') if user['last_activity'] else '-')
        worksheet.write(row, 5, 'Да' if user['has_application'] > 0 else 'Нет')
        worksheet.write(row, 6, user['referrals_count'])
        worksheet.write(row, 7, f"Источник {user['source_id']}" if user['source_id'] else 'Прямой')
    
    workbook.close()
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'users_{get_local_time().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Удаляем в правильном порядке из-за foreign keys
        cur.execute("DELETE FROM user_actions WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM referrals WHERE referrer_id = %s OR referred_id = %s", (user_id, user_id))
        cur.execute("DELETE FROM applications WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM bot_users WHERE user_id = %s", (user_id,))
        
        conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/editor')
@login_required
def text_editor():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bot_texts ORDER BY category, key")
    texts = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('editor.html', texts=texts)

@app.route('/admin/texts/<int:text_id>')
@login_required
def get_text(text_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bot_texts WHERE id = %s", (text_id,))
    text = cur.fetchone()
    cur.close()
    conn.close()
    
    if text:
        return jsonify(dict(text))
    return jsonify({'error': 'Text not found'}), 404

@app.route('/admin/texts/<int:text_id>/update', methods=['POST'])
@login_required
def update_text(text_id):
    text_content = request.form.get('text')
    
    if not text_content:
        return jsonify({'error': 'Text is required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE bot_texts 
            SET text = %s, updated_at = CURRENT_TIMESTAMP, updated_by = %s
            WHERE id = %s
        """, (text_content, current_user.id, text_id))
        
        conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/texts/<key>')
def get_text_by_key(key):
    # Простая защита по API ключу
    api_key = request.headers.get('X-API-Key')
    if api_key != 'internal-bot-key-2024':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT text FROM bot_texts WHERE key = %s", (key,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    if result:
        return jsonify({'text': result['text']})
    return jsonify({'error': 'Text not found'}), 404

@app.route('/broadcast')
@login_required
def broadcast():
    return render_template('broadcast.html')

@app.route('/traffic-sources')
@login_required
def traffic_sources():
    return render_template('traffic_sources.html')

@app.route('/system')
@login_required
def system():
    return render_template('system.html')

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
