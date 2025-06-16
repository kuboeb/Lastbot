from flask import render_template, jsonify, request
from flask_login import login_required
import psycopg2
from psycopg2.extras import RealDictCursor

def register_richads_routes(app, get_db_connection):
    """Регистрация маршрутов RichAds"""
    
    @app.route('/richads/')
    @login_required
    def richads_dashboard():
        """Дашборд RichAds конверсий"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Статистика
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'sent' THEN 1 END) as sent,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                SUM(CASE WHEN status = 'sent' THEN payout ELSE 0 END) as total_payout
            FROM richads_conversions
        """)
        stats = cur.fetchone()
        
        # Последние конверсии с успешной отправкой
        cur.execute("""
            SELECT 
                rc.id,
                rc.application_id,
                rc.click_id,
                rc.campaign,
                rc.payout,
                rc.status,
                rc.response_status,
                rc.created_at,
                rc.request_sent_at,
                a.full_name,
                a.phone,
                a.country,
                bu.username
            FROM richads_conversions rc
            JOIN applications a ON rc.application_id = a.id
            JOIN bot_users bu ON a.user_id = bu.user_id
            WHERE rc.status = 'sent'
            ORDER BY rc.created_at DESC
            LIMIT 100
        """)
        successful_conversions = cur.fetchall()
        
        # Все конверсии для таблицы
        cur.execute("""
            SELECT 
                rc.*,
                a.full_name,
                a.phone,
                bu.username
            FROM richads_conversions rc
            JOIN applications a ON rc.application_id = a.id
            JOIN bot_users bu ON a.user_id = bu.user_id
            ORDER BY rc.created_at DESC
            LIMIT 50
        """)
        all_conversions = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('richads/dashboard.html', 
                             stats=stats, 
                             successful_conversions=successful_conversions,
                             all_conversions=all_conversions)
    
    @app.route('/richads/retry/<int:conversion_id>', methods=['POST'])
    @login_required
    def retry_richads_conversion(conversion_id):
        """Повторная отправка конверсии"""
        try:
            from utils.richads.sender import _send_richads_conversion
            
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Получаем application_id
            cur.execute("SELECT application_id FROM richads_conversions WHERE id = %s", (conversion_id,))
            result = cur.fetchone()
            
            if result:
                _send_richads_conversion(result['application_id'])
                return jsonify({'success': True, 'message': 'Конверсия отправлена повторно'})
            else:
                return jsonify({'success': False, 'message': 'Конверсия не найдена'}), 404
                
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
