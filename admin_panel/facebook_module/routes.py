from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required
from . import facebook_bp
from .models import (
    check_facebook_tables,  # Изменено с create_facebook_tables
    get_facebook_conversions,
    get_facebook_stats
)
from .services import retry_failed_conversions
from .models import get_db_connection
import psycopg2.extras

# Проверяем таблицы при импорте
check_facebook_tables()

@facebook_bp.route('/')
@facebook_bp.route('/conversions')
@login_required
def conversions_list():
    """Список Facebook конверсий"""
    # Получаем фильтры
    filters = {
        'status': request.args.get('status'),
        'date_from': request.args.get('date_from'),
        'date_to': request.args.get('date_to'),
        'source_id': request.args.get('source_id')
    }
    
    # Получаем данные
    conversions = get_facebook_conversions(filters)
    stats = get_facebook_stats()
    
    # Получаем список источников для фильтра
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, name FROM traffic_sources 
        WHERE platform = 'facebook' AND is_active = true
        ORDER BY name
    """)
    sources = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('facebook/conversions.html',
                         conversions=conversions,
                         stats=stats,
                         sources=sources,
                         filters=filters)

@facebook_bp.route('/conversions/<int:conversion_id>')
@login_required
def conversion_detail(conversion_id):
    """Детальная информация о конверсии"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("""
        SELECT 
            fc.*,
            a.full_name,
            a.phone,
            a.country,
            a.preferred_time,
            a.created_at as application_date,
            bu.username,
            bu.user_id,
            ts.name as source_name,
            uc.click_id,
            uc.created_at as click_date
        FROM facebook_conversions fc
        JOIN applications a ON fc.application_id = a.id
        JOIN bot_users bu ON a.user_id = bu.user_id
        LEFT JOIN traffic_sources ts ON bu.source_id = ts.id
        LEFT JOIN user_clicks uc ON bu.user_id = uc.user_id AND uc.click_type = 'fbclid'
        WHERE fc.id = %s
    """, (conversion_id,))
    
    conversion = cur.fetchone()
    cur.close()
    conn.close()
    
    if not conversion:
        flash('Конверсия не найдена', 'error')
        return redirect(url_for('facebook.conversions_list'))
    
    return render_template('facebook/conversion_detail.html',
                         conversion=conversion)

@facebook_bp.route('/retry-failed', methods=['POST'])
@login_required
def retry_failed():
    """Повторная отправка неудачных конверсий"""
    result = retry_failed_conversions()
    
    flash(f"Повторная отправка: {result['successful']} успешно, {result['failed']} неудачно", 
          'info')
    
    return redirect(url_for('facebook.conversions_list'))

@facebook_bp.route('/stats')
@login_required
def stats():
    """Статистика Facebook конверсий"""
    stats = get_facebook_stats()
    
    # Дополнительная статистика по дням
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("""
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'success' THEN 1 END) as success,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
        FROM facebook_conversions
        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    """)
    
    daily_stats = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('facebook/stats.html',
                         stats=stats,
                         daily_stats=daily_stats)
