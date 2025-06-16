import psycopg2
import psycopg2.extras
from datetime import datetime
import json
import sys
import os

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Импортируем функцию подключения к БД из app.py админки
def get_db_connection():
    """Функция подключения к БД"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'crypto_course_db'),
        user=os.getenv('DB_USER', 'cryptobot'),
        password=os.getenv('DB_PASSWORD', 'kuboeb1A')
    )

def check_facebook_tables():
    """Проверка существования таблиц для Facebook трекинга"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Проверяем существование таблиц
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'user_clicks'
            );
        """)
        user_clicks_exists = cur.fetchone()[0]
        
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'facebook_conversions'
            );
        """)
        fb_conversions_exists = cur.fetchone()[0]
        
        if user_clicks_exists and fb_conversions_exists:
            print("✅ Facebook таблицы существуют")
        else:
            print("⚠️ Некоторые таблицы отсутствуют")
            
    except Exception as e:
        print(f"❌ Ошибка проверки таблиц: {e}")
    finally:
        cur.close()
        conn.close()

# Вызываем проверку вместо создания
check_facebook_tables()

def save_user_click(user_id, click_id, click_type='fbclid', raw_params=None):
    """Сохранение click ID пользователя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO user_clicks (user_id, click_id, click_type, raw_params)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, click_type) 
            DO UPDATE SET 
                click_id = EXCLUDED.click_id,
                raw_params = EXCLUDED.raw_params,
                created_at = CURRENT_TIMESTAMP
        """, (user_id, click_id, click_type, raw_params))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка сохранения click_id: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def get_user_click_id(user_id, click_type='fbclid'):
    """Получение click ID пользователя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT click_id FROM user_clicks 
            WHERE user_id = %s AND click_type = %s
            ORDER BY created_at DESC LIMIT 1
        """, (user_id, click_type))
        
        result = cur.fetchone()
        return result[0] if result else None
    finally:
        cur.close()
        conn.close()

def save_conversion_log(application_id, event_id, request_data, response_data=None, 
                       status='pending', error_message=None):
    """Сохранение лога отправки конверсии"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO facebook_conversions 
            (application_id, event_id, pixel_id, status, request_data, 
             response_data, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (event_id) DO UPDATE SET
                status = EXCLUDED.status,
                response_data = EXCLUDED.response_data,
                error_message = EXCLUDED.error_message
        """, (
            application_id, 
            event_id,
            request_data.get('pixel_id') if isinstance(request_data, dict) else None,
            status,
            json.dumps(request_data),
            json.dumps(response_data) if response_data else None,
            error_message
        ))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка сохранения лога конверсии: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def get_facebook_conversions(filters=None):
    """Получение списка Facebook конверсий с фильтрами"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Сначала проверим, есть ли вообще Facebook источники
    cur.execute("""
        SELECT COUNT(*) as count FROM traffic_sources WHERE platform = 'facebook'
    """)
    fb_sources_count = cur.fetchone()['count']
    
    if fb_sources_count == 0:
        # Если нет Facebook источников, возвращаем пустой результат
        cur.close()
        conn.close()
        return []
    
    query = """
        SELECT 
            fc.*,
            a.full_name,
            a.phone,
            a.country,
            a.created_at as application_date,
            bu.username,
            ts.name as source_name
        FROM facebook_conversions fc
        JOIN applications a ON fc.application_id = a.id
        JOIN bot_users bu ON a.user_id = bu.user_id
        LEFT JOIN traffic_sources ts ON bu.source_id = ts.id
        WHERE 1=1
    """
    
    # Добавляем фильтры
    conditions = []
    params = []
    
    if filters:
        if filters.get('status'):
            conditions.append("fc.status = %s")
            params.append(filters['status'])
        
        if filters.get('date_from'):
            conditions.append("fc.created_at >= %s")
            params.append(filters['date_from'])
        
        if filters.get('date_to'):
            conditions.append("fc.created_at <= %s")
            params.append(filters['date_to'])
        
        if filters.get('source_id'):
            conditions.append("ts.id = %s")
            params.append(filters['source_id'])
    
    if conditions:
        query += " AND " + " AND ".join(conditions)
    
    query += " ORDER BY fc.created_at DESC LIMIT 100"
    
    cur.execute(query, params)
    results = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return results

def get_facebook_stats():
    """Получение статистики по Facebook конверсиям"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Общая статистика
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'success' THEN 1 END) as success,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending
        FROM facebook_conversions
        WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
    """)
    
    stats = cur.fetchone()
    
    # Статистика по источникам
    cur.execute("""
        SELECT 
            ts.name as source_name,
            ts.id as source_id,
            COUNT(fc.id) as total_conversions,
            COUNT(CASE WHEN fc.status = 'success' THEN 1 END) as success_count,
            CASE 
                WHEN COUNT(fc.id) > 0 THEN
                    ROUND(
                        COUNT(CASE WHEN fc.status = 'success' THEN 1 END)::numeric / 
                        COUNT(fc.id) * 100, 1
                    )
                ELSE 0
            END as success_rate
        FROM traffic_sources ts
        LEFT JOIN bot_users bu ON ts.id = bu.source_id
        LEFT JOIN applications a ON bu.user_id = a.user_id
        LEFT JOIN facebook_conversions fc ON a.id = fc.application_id
        WHERE ts.platform = 'facebook'
        GROUP BY ts.id, ts.name
        ORDER BY total_conversions DESC
    """)
    
    sources_stats = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return {
        'total_stats': stats,
        'sources_stats': sources_stats
    }
