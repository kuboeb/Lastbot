import re

with open('app.py', 'r') as f:
    content = f.read()

# Найдем функцию delete_user и заменим её
old_function = re.search(r'def delete_user\(user_id\):.*?(?=\n@app\.route|\ndef |\nif __name__|$)', content, re.DOTALL)

if old_function:
    new_function = '''def delete_user(user_id):
    """Полное каскадное удаление пользователя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Проверяем существование пользователя
        cur.execute("SELECT username FROM bot_users WHERE user_id = %s", (user_id,))
        user = cur.fetchone()
        
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        username = user['username'] or f'ID: {user_id}'
        
        # Удаляем в правильном порядке
        # 1. user_actions
        cur.execute("DELETE FROM user_actions WHERE user_id = %s", (user_id,))
        
        # 2. tracking_events
        cur.execute("DELETE FROM tracking_events WHERE user_id = %s", (user_id,))
        
        # 3. user_clicks и user_click_ids
        cur.execute("DELETE FROM user_clicks WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM user_click_ids WHERE user_id = %s", (user_id,))
        
        # 4. broadcast_recipients
        cur.execute("DELETE FROM broadcast_recipients WHERE user_id = %s", (user_id,))
        
        # 5. operator_messages
        cur.execute("DELETE FROM operator_messages WHERE user_id = %s", (user_id,))
        
        # 6. conversion_logs
        cur.execute("DELETE FROM conversion_logs WHERE user_id = %s", (user_id,))
        
        # 7. inline_states
        cur.execute("DELETE FROM inline_states WHERE user_id = %s", (user_id,))
        
        # 8. referrals (как referrer и как referred)
        cur.execute("DELETE FROM referrals WHERE referrer_id = %s OR referred_id = %s", (user_id, user_id))
        
        # 9. Обновляем applications - убираем referrer_id
        cur.execute("UPDATE applications SET referrer_id = NULL WHERE referrer_id = %s", (user_id,))
        
        # 10. Удаляем applications пользователя
        cur.execute("DELETE FROM applications WHERE user_id = %s", (user_id,))
        
        # 11. Наконец удаляем самого пользователя
        cur.execute("DELETE FROM bot_users WHERE user_id = %s", (user_id,))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'Пользователь {username} и все связанные данные удалены'
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': f'Ошибка при удалении: {str(e)}'}), 500
    finally:
        cur.close()
        conn.close()'''
    
    content = content[:old_function.start()] + new_function + content[old_function.end():]

with open('app.py', 'w') as f:
    f.write(content)

print("Updated delete_user function for complete cascade deletion")
