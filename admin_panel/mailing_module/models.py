import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json

class MailingModel:
    def __init__(self, db_connection_func):
        self.get_db_connection = db_connection_func
    
    def get_all_mailings(self):
        """Получить все рассылки из новой таблицы"""
        conn = self.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            # Сначала проверим, существует ли таблица
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'mailings'
                )
            """)
            
            if not cur.fetchone()['exists']:
                # Создаем таблицу если её нет
                self._create_mailings_table(conn)
            
            # Получаем данные
            cur.execute("""
                SELECT 
                    m.*,
                    COUNT(DISTINCT mr.user_id) as recipient_count,
                    COUNT(DISTINCT CASE WHEN mr.status = 'sent' THEN mr.user_id END) as sent_count
                FROM mailings m
                LEFT JOIN mailing_recipients mr ON m.id = mr.mailing_id
                GROUP BY m.id
                ORDER BY m.created_at DESC
            """)
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()
    
    def _create_mailings_table(self, conn):
        """Создать таблицы для рассылок"""
        cur = conn.cursor()
        try:
            # Таблица рассылок
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mailings (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200),
                    message TEXT,
                    audience_type VARCHAR(50),
                    status VARCHAR(20) DEFAULT 'draft',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_at TIMESTAMP,
                    recipient_count INTEGER DEFAULT 0
                )
            """)
            
            # Таблица получателей
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mailing_recipients (
                    id SERIAL PRIMARY KEY,
                    mailing_id INTEGER REFERENCES mailings(id) ON DELETE CASCADE,
                    user_id BIGINT,
                    status VARCHAR(20) DEFAULT 'pending',
                    sent_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(mailing_id, user_id)
                )
            """)
            
            conn.commit()
        finally:
            cur.close()
    
    def create_mailing(self, name, message, audience_type):
        """Создать новую рассылку"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        try:
            # Создаем рассылку
            cur.execute("""
                INSERT INTO mailings (name, message, audience_type)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (name, message, audience_type))
            
            mailing_id = cur.fetchone()[0]
            
            # Добавляем получателей
            if audience_type == 'all':
                cur.execute("""
                    INSERT INTO mailing_recipients (mailing_id, user_id)
                    SELECT %s, user_id FROM bot_users WHERE is_blocked = FALSE
                    ON CONFLICT DO NOTHING
                """, (mailing_id,))
            elif audience_type == 'no_application':
                cur.execute("""
                    INSERT INTO mailing_recipients (mailing_id, user_id)
                    SELECT %s, user_id FROM bot_users 
                    WHERE is_blocked = FALSE AND has_application = FALSE
                    ON CONFLICT DO NOTHING
                """, (mailing_id,))
            elif audience_type == 'with_application':
                cur.execute("""
                    INSERT INTO mailing_recipients (mailing_id, user_id)
                    SELECT %s, user_id FROM bot_users 
                    WHERE is_blocked = FALSE AND has_application = TRUE
                    ON CONFLICT DO NOTHING
                """, (mailing_id,))
            
            # Обновляем количество
            cur.execute("""
                UPDATE mailings 
                SET recipient_count = (
                    SELECT COUNT(*) FROM mailing_recipients WHERE mailing_id = %s
                )
                WHERE id = %s
            """, (mailing_id, mailing_id))
            
            conn.commit()
            return mailing_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
    
    def get_mailing_stats(self, mailing_id):
        """Получить статистику рассылки"""
        conn = self.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT 
                    m.*,
                    COUNT(DISTINCT mr.user_id) as total_recipients,
                    COUNT(DISTINCT CASE WHEN mr.status = 'sent' THEN mr.user_id END) as sent,
                    COUNT(DISTINCT CASE WHEN mr.status = 'failed' THEN mr.user_id END) as failed
                FROM mailings m
                LEFT JOIN mailing_recipients mr ON m.id = mr.mailing_id
                WHERE m.id = %s
                GROUP BY m.id
            """, (mailing_id,))
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()
    
    def update_mailing_status(self, mailing_id, status):
        """Обновить статус рассылки"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        try:
            if status == 'sent':
                cur.execute("""
                    UPDATE mailings 
                    SET status = %s, sent_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (status, mailing_id))
            else:
                cur.execute("""
                    UPDATE mailings 
                    SET status = %s 
                    WHERE id = %s
                """, (status, mailing_id))
            
            conn.commit()
        finally:
            cur.close()
            conn.close()
    
    def get_audience_count(self, audience_type):
        """Получить количество получателей"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        try:
            if audience_type == 'all':
                cur.execute("SELECT COUNT(*) FROM bot_users WHERE is_blocked = FALSE")
            elif audience_type == 'no_application':
                cur.execute("SELECT COUNT(*) FROM bot_users WHERE is_blocked = FALSE AND has_application = FALSE")
            elif audience_type == 'with_application':
                cur.execute("SELECT COUNT(*) FROM bot_users WHERE is_blocked = FALSE AND has_application = TRUE")
            else:
                return 0
            
            return cur.fetchone()[0]
        finally:
            cur.close()
            conn.close()

    def get_mailing_recipients(self, mailing_id):
        """Получить список получателей рассылки"""
        conn = self.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT 
                    mr.user_id,
                    bu.username,
                    mr.status
                FROM mailing_recipients mr
                JOIN bot_users bu ON mr.user_id = bu.user_id
                WHERE mr.mailing_id = %s AND mr.status = 'pending'
                AND bu.is_blocked = FALSE
            """, (mailing_id,))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()
    
    def update_recipient_status(self, mailing_id, user_id, status):
        """Обновить статус получателя"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE mailing_recipients 
                SET status = %s, sent_at = CURRENT_TIMESTAMP
                WHERE mailing_id = %s AND user_id = %s
            """, (status, mailing_id, user_id))
            conn.commit()
        finally:
            cur.close()
            conn.close()
    
    def update_mailing_stats(self, mailing_id, sent_count, failed_count):
        """Обновить статистику рассылки"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE mailings 
                SET sent_count = %s, failed_count = %s
                WHERE id = %s
            """, (sent_count, failed_count, mailing_id))
            conn.commit()
        finally:
            cur.close()
            conn.close()

    def delete_mailing(self, mailing_id, force=False):
        """Удалить рассылку"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        try:
            if force:
                # Принудительное удаление для админа
                cur.execute("""
                    DELETE FROM mailings 
                    WHERE id = %s
                    RETURNING id
                """, (mailing_id,))
            else:
                # Обычное удаление - только черновики и отправленные
                cur.execute("""
                    DELETE FROM mailings 
                    WHERE id = %s AND status IN ('draft', 'sent')
                    RETURNING id
                """, (mailing_id,))
            
            deleted = cur.fetchone()
            conn.commit()
            return deleted is not None
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()