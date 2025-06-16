import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json

class BroadcastModel:
    def __init__(self, db_connection_func):
        self.get_db_connection = db_connection_func
    
    def get_all_broadcasts(self):
        """Получить все рассылки"""
        conn = self.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT 
                    b.*,
                    COUNT(DISTINCT br.user_id) as recipient_count,
                    COUNT(DISTINCT CASE WHEN br.status = 'sent' THEN br.user_id END) as sent_count,
                    COUNT(DISTINCT CASE WHEN br.delivered = true THEN br.user_id END) as delivered_count
                FROM broadcasts b
                LEFT JOIN broadcast_recipients br ON b.id = br.broadcast_id
                GROUP BY b.id
                ORDER BY b.created_at DESC
            """)
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()
    
    def create_broadcast(self, name, message, audience_type, scenario_type=None):
        """Создать новую рассылку"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        try:
            # Создаем рассылку
            cur.execute("""
                INSERT INTO broadcasts (name, message, target_audience, status, scenario_type)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (name, message, json.dumps({'type': audience_type}), 'draft', scenario_type))
            
            broadcast_id = cur.fetchone()[0]
            
            # Добавляем получателей в зависимости от аудитории
            if audience_type == 'all':
                cur.execute("""
                    INSERT INTO broadcast_recipients (broadcast_id, user_id)
                    SELECT %s, user_id FROM bot_users WHERE is_blocked = FALSE
                """, (broadcast_id,))
            elif audience_type == 'no_application':
                cur.execute("""
                    INSERT INTO broadcast_recipients (broadcast_id, user_id)
                    SELECT %s, user_id FROM bot_users 
                    WHERE is_blocked = FALSE AND has_application = FALSE
                """, (broadcast_id,))
            elif audience_type == 'with_application':
                cur.execute("""
                    INSERT INTO broadcast_recipients (broadcast_id, user_id)
                    SELECT %s, user_id FROM bot_users 
                    WHERE is_blocked = FALSE AND has_application = TRUE
                """, (broadcast_id,))
            
            # Обновляем количество получателей
            cur.execute("""
                UPDATE broadcasts 
                SET recipient_count = (
                    SELECT COUNT(*) FROM broadcast_recipients WHERE broadcast_id = %s
                )
                WHERE id = %s
            """, (broadcast_id, broadcast_id))
            
            conn.commit()
            return broadcast_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
    
    def get_broadcast_stats(self, broadcast_id):
        """Получить статистику рассылки"""
        conn = self.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT 
                    b.*,
                    COUNT(DISTINCT br.user_id) as total_recipients,
                    COUNT(DISTINCT CASE WHEN br.status = 'sent' THEN br.user_id END) as sent,
                    COUNT(DISTINCT CASE WHEN br.delivered = true THEN br.user_id END) as delivered,
                    COUNT(DISTINCT CASE WHEN br.status = 'failed' THEN br.user_id END) as failed
                FROM broadcasts b
                LEFT JOIN broadcast_recipients br ON b.id = br.broadcast_id
                WHERE b.id = %s
                GROUP BY b.id
            """, (broadcast_id,))
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()
    
    def update_broadcast_status(self, broadcast_id, status):
        """Обновить статус рассылки"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        try:
            if status == 'sending':
                cur.execute("""
                    UPDATE broadcasts 
                    SET status = %s, started_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (status, broadcast_id))
            elif status == 'sent':
                cur.execute("""
                    UPDATE broadcasts 
                    SET status = %s, sent_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (status, broadcast_id))
            else:
                cur.execute("""
                    UPDATE broadcasts 
                    SET status = %s 
                    WHERE id = %s
                """, (status, broadcast_id))
            
            conn.commit()
        finally:
            cur.close()
            conn.close()
    
    def get_audience_preview(self, audience_type):
        """Получить превью аудитории"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        try:
            if audience_type == 'all':
                cur.execute("SELECT COUNT(*) FROM bot_users WHERE is_blocked = FALSE")
            elif audience_type == 'no_application':
                cur.execute("SELECT COUNT(*) FROM bot_users WHERE is_blocked = FALSE AND has_application = FALSE")
            elif audience_type == 'with_application':
                cur.execute("SELECT COUNT(*) FROM bot_users WHERE is_blocked = FALSE AND has_application = TRUE")
            
            count = cur.fetchone()[0]
            return count
        finally:
            cur.close()
            conn.close()
    
    def delete_broadcast(self, broadcast_id):
        """Удалить рассылку"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM broadcasts WHERE id = %s AND status = 'draft'", (broadcast_id,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            cur.close()
            conn.close()
