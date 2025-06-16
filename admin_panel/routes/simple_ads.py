from flask import render_template, request, jsonify, redirect, url_for, Response
from flask_login import login_required
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import json
import re
import csv
from io import StringIO

def register_simple_ads_routes(app, get_db_connection):
    """Регистрация маршрутов для простых рекламных ссылок"""
    
    @app.route('/simple-ads/')
    @login_required
    def simple_ads_dashboard():
        """Главная страница рекламных ссылок"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Получаем период из параметров или последние 30 дней
        date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
        
        # Получаем статистику по всем ссылкам
        cur.execute("""
            SELECT 
                sa.id,
                sa.name,
                sa.code,
                sa.budget,
                sa.is_active,
                COUNT(DISTINCT CASE WHEN ac.event_type = 'start' THEN ac.user_id END) as starts,
                COUNT(DISTINCT CASE WHEN ac.event_type = 'application' THEN ac.user_id END) as applications,
                COUNT(DISTINCT ac.user_id) as unique_users
            FROM simple_ads sa
            LEFT JOIN ad_clicks ac ON sa.id = ac.ad_id 
                AND ac.created_at >= %s::date 
                AND ac.created_at < %s::date + interval '1 day'
            GROUP BY sa.id, sa.name, sa.code, sa.budget, sa.is_active
            ORDER BY sa.created_at DESC
        """, (date_from, date_to))
        
        ads = cur.fetchall()
        
        # Добавляем расчет конверсии и CPL
        for ad in ads:
            if ad['starts'] > 0:
                ad['conversion_rate'] = round((ad['applications'] / ad['starts']) * 100, 1)
            else:
                ad['conversion_rate'] = 0
                
            if ad['budget'] and ad['applications'] > 0:
                ad['cpl'] = round(float(ad['budget']) / ad['applications'], 2)
            else:
                ad['cpl'] = None
        
        cur.close()
        conn.close()
        
        return render_template('simple_ads/dashboard.html', 
                             ads=ads, 
                             date_from=date_from, 
                             date_to=date_to)
    
    @app.route('/simple-ads/create', methods=['GET', 'POST'])
    @login_required
    def create_simple_ad():
        """Создание новой рекламной ссылки"""
        if request.method == 'POST':
            data = request.json
            
            # Генерация кода из названия
            name = data.get('name', '')
            code = data.get('code', '')
            
            if not code:
                # Автогенерация кода
                code = 'ad_' + re.sub(r'[^a-z0-9]+', '_', name.lower())[:50]
                code = re.sub(r'_+', '_', code).strip('_')
            
            conn = get_db_connection()
            cur = conn.cursor()
            
            try:
                cur.execute("""
                    INSERT INTO simple_ads (name, code, description, budget)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (
                    data.get('name'),
                    code,
                    data.get('description', ''),
                    data.get('budget') if data.get('budget') else None
                ))
                
                ad_id = cur.fetchone()['id']
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'id': ad_id,
                    'code': code,
                    'link': f"https://t.me/cryplace_bot?start={code}"
                })
                
            except psycopg2.IntegrityError:
                return jsonify({
                    'success': False,
                    'error': 'Код уже существует'
                }), 400
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
            finally:
                cur.close()
                conn.close()
        
        return render_template('simple_ads/create.html')
    
    @app.route('/simple-ads/<int:ad_id>/details')
    @login_required
    def simple_ad_details(ad_id):
        """Детальная страница рекламной ссылки"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Получаем информацию о ссылке
        cur.execute("SELECT * FROM simple_ads WHERE id = %s", (ad_id,))
        ad = cur.fetchone()
        
        if not ad:
            return redirect(url_for('simple_ads_dashboard'))
        
        # Получаем статистику по дням
        cur.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(DISTINCT CASE WHEN event_type = 'start' THEN user_id END) as starts,
                COUNT(DISTINCT CASE WHEN event_type = 'application' THEN user_id END) as applications
            FROM ad_clicks
            WHERE ad_id = %s
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            LIMIT 30
        """, (ad_id,))
        
        daily_stats = cur.fetchall()
        
        # Получаем общую статистику
        cur.execute("""
            SELECT 
                COUNT(DISTINCT CASE WHEN event_type = 'start' THEN user_id END) as total_starts,
                COUNT(DISTINCT CASE WHEN event_type = 'application' THEN user_id END) as total_applications,
                COUNT(DISTINCT user_id) as unique_users
            FROM ad_clicks
            WHERE ad_id = %s
        """, (ad_id,))
        
        stats = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return render_template('simple_ads/details.html', 
                             ad=ad, 
                             daily_stats=daily_stats,
                             stats=stats)
    
    @app.route('/simple-ads/<int:ad_id>/leads')
    @login_required
    def simple_ad_leads(ad_id):
        """Список лидов от рекламной ссылки"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Получаем информацию о ссылке
        cur.execute("SELECT * FROM simple_ads WHERE id = %s", (ad_id,))
        ad = cur.fetchone()
        
        if not ad:
            return redirect(url_for('simple_ads_dashboard'))
        
        # Фильтры
        status_filter = request.args.get('status', 'all')
        country_filter = request.args.get('country', '')
        search_query = request.args.get('search', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # Базовый запрос
        query = """
            SELECT DISTINCT
                bu.user_id,
                bu.username,
                bu.first_seen,
                a.id as application_id,
                a.full_name,
                a.phone,
                a.country,
                a.created_at as application_date,
                CASE WHEN a.id IS NOT NULL THEN true ELSE false END as has_application
            FROM ad_clicks ac
            JOIN bot_users bu ON ac.user_id = bu.user_id
            LEFT JOIN applications a ON bu.user_id = a.user_id
            WHERE ac.ad_id = %s
        """
        
        params = [ad_id]
        
        # Применяем фильтры
        if status_filter == 'applications':
            query += " AND a.id IS NOT NULL"
        elif status_filter == 'starts_only':
            query += " AND a.id IS NULL"
            
        if country_filter:
            query += " AND a.country = %s"
            params.append(country_filter)
            
        if search_query:
            query += " AND (a.full_name ILIKE %s OR a.phone ILIKE %s OR bu.username ILIKE %s)"
            search_pattern = f"%{search_query}%"
            params.extend([search_pattern, search_pattern, search_pattern])
            
        if date_from:
            query += " AND bu.first_seen >= %s"
            params.append(date_from)
            
        if date_to:
            query += " AND bu.first_seen <= %s"
            params.append(date_to)
            
        query += " ORDER BY bu.first_seen DESC"
        
        cur.execute(query, params)
        leads = cur.fetchall()
        
        # Получаем список стран для фильтра
        cur.execute("""
            SELECT DISTINCT a.country 
            FROM ad_clicks ac
            JOIN applications a ON ac.user_id = a.user_id
            WHERE ac.ad_id = %s AND a.country IS NOT NULL
            ORDER BY a.country
        """, (ad_id,))
        
        countries = [row['country'] for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        return render_template('simple_ads/leads.html', 
                             ad=ad, 
                             leads=leads,
                             countries=countries,
                             filters={
                                 'status': status_filter,
                                 'country': country_filter,
                                 'search': search_query,
                                 'date_from': date_from,
                                 'date_to': date_to
                             })
    
    @app.route('/simple-ads/compare')
    @login_required
    def compare_simple_ads():
        """Сравнение эффективности рекламных кампаний"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Получаем период
        date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
        
        # Получаем сравнительную статистику
        cur.execute("""
            SELECT 
                sa.id,
                sa.name,
                sa.budget,
                COUNT(DISTINCT CASE WHEN ac.event_type = 'start' THEN ac.user_id END) as starts,
                COUNT(DISTINCT CASE WHEN ac.event_type = 'application' THEN ac.user_id END) as applications,
                sa.budget::numeric / NULLIF(COUNT(DISTINCT CASE WHEN ac.event_type = 'application' THEN ac.user_id END), 0) as cpl
            FROM simple_ads sa
            LEFT JOIN ad_clicks ac ON sa.id = ac.ad_id
                AND ac.created_at >= %s::date 
                AND ac.created_at < %s::date + interval '1 day'
            WHERE sa.is_active = true
            GROUP BY sa.id, sa.name, sa.budget
            HAVING COUNT(DISTINCT ac.user_id) > 0
            ORDER BY applications DESC
        """, (date_from, date_to))
        
        ads_comparison = cur.fetchall()
        
        # Находим лучший источник по CPL
        best_cpl_ad = None
        if ads_comparison:
            valid_ads = [ad for ad in ads_comparison if ad['cpl'] is not None]
            if valid_ads:
                best_cpl_ad = min(valid_ads, key=lambda x: x['cpl'])
        
        # Общая статистика
        cur.execute("""
            SELECT 
                SUM(sa.budget) as total_budget,
                COUNT(DISTINCT ac.user_id) as total_users,
                COUNT(DISTINCT CASE WHEN ac.event_type = 'application' THEN ac.user_id END) as total_applications
            FROM simple_ads sa
            LEFT JOIN ad_clicks ac ON sa.id = ac.ad_id
                AND ac.created_at >= %s::date 
                AND ac.created_at < %s::date + interval '1 day'
            WHERE sa.is_active = true
        """, (date_from, date_to))
        
        totals = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return render_template('simple_ads/compare.html',
                             ads_comparison=ads_comparison,
                             best_cpl_ad=best_cpl_ad,
                             totals=totals,
                             date_from=date_from,
                             date_to=date_to)
    
    @app.route('/simple-ads/<int:ad_id>/toggle', methods=['POST'])
    @login_required
    def toggle_simple_ad(ad_id):
        """Включение/отключение рекламной ссылки"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                UPDATE simple_ads 
                SET is_active = NOT is_active, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING is_active
            """, (ad_id,))
            
            result = cur.fetchone()
            conn.commit()
            
            return jsonify({
                'success': True,
                'is_active': result['is_active']
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
        finally:
            cur.close()
            conn.close()
    
    @app.route('/simple-ads/export/<int:ad_id>')
    @login_required
    def export_simple_ad_leads(ad_id):
        """Экспорт лидов в CSV"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Получаем данные для экспорта
        cur.execute("""
            SELECT 
                bu.user_id,
                bu.username,
                a.full_name,
                a.phone,
                a.country,
                a.created_at,
                CASE WHEN a.id IS NOT NULL THEN 'Заявка' ELSE 'Только старт' END as status
            FROM ad_clicks ac
            JOIN bot_users bu ON ac.user_id = bu.user_id
            LEFT JOIN applications a ON bu.user_id = a.user_id
            WHERE ac.ad_id = %s
            ORDER BY bu.first_seen DESC
        """, (ad_id,))
        
        leads = cur.fetchall()
        
        # Создаем CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow(['User ID', 'Username', 'Имя', 'Телефон', 'Страна', 'Дата', 'Статус'])
        
        # Данные
        for lead in leads:
            writer.writerow([
                lead['user_id'],
                lead['username'] or '',
                lead['full_name'] or '',
                lead['phone'] or '',
                lead['country'] or '',
                lead['created_at'].strftime('%Y-%m-%d %H:%M') if lead['created_at'] else '',
                lead['status']
            ])
        
        output.seek(0)
        cur.close()
        conn.close()
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=leads_ad_{ad_id}.csv'
            }
        )
