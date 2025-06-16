from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required
from . import mailing_bp
from .models import MailingModel
from .services import MailingService
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Глобальные переменные для моделей
mailing_model = None
mailing_service = None

def get_db_connection():
    """Получить подключение к БД"""
    return psycopg2.connect(
        host='localhost',
        database='crypto_course_db',
        user='cryptobot',
        password='kuboeb1A'
    )

# Инициализируем модели при импорте
mailing_model = MailingModel(get_db_connection)
mailing_service = MailingService(None, mailing_model)  # bot_instance добавим позже

@mailing_bp.route('/')
@login_required
def index():
    """Список всех рассылок"""
    try:
        mailings = mailing_model.get_all_mailings()
        return render_template('mailing/list.html', mailings=mailings)
    except Exception as e:
        flash(f'Ошибка: {str(e)}', 'danger')
        return render_template('mailing/list.html', mailings=[])

@mailing_bp.route('/create')
@login_required
def create():
    """Страница создания рассылки"""
    return render_template('mailing/create.html')

@mailing_bp.route('/create', methods=['POST'])
@login_required
def create_post():
    """Создание новой рассылки"""
    try:
        data = request.get_json()
        
        mailing_id = mailing_model.create_mailing(
            name=data.get('name', 'Без названия'),
            message=data.get('message', ''),
            audience_type=data.get('audience', 'all')
        )
        
        return jsonify({'success': True, 'mailing_id': mailing_id})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@mailing_bp.route('/<int:mailing_id>/stats')
@login_required
def stats(mailing_id):
    """Статистика рассылки"""
    try:
        stats = mailing_model.get_mailing_stats(mailing_id)
        if not stats:
            flash('Рассылка не найдена', 'danger')
            return redirect(url_for('mailing.index'))
        
        return render_template('mailing/stats.html', mailing=stats)
    except Exception as e:
        flash(f'Ошибка: {str(e)}', 'danger')
        return redirect(url_for('mailing.index'))

@mailing_bp.route('/<int:mailing_id>/send', methods=['POST'])
@login_required
def send(mailing_id):
    """Отправить рассылку"""
    try:
        # Простая заглушка для отправки
        mailing_model.update_mailing_status(mailing_id, 'sent')
        return jsonify({'success': True, 'message': 'Рассылка отправлена'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@mailing_bp.route('/preview', methods=['POST'])
@login_required
def preview():
    """Предпросмотр аудитории"""
    try:
        audience_type = request.json.get('audience', 'all')
        count = mailing_model.get_audience_count(audience_type)
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
