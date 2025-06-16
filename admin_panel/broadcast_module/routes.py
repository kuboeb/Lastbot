from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from . import broadcast_bp
from .models import BroadcastModel
from .services import BroadcastService
import json

# Эти объекты будут инициализированы из основного приложения
broadcast_model = None
broadcast_service = None

def init_broadcast_module(app, db_connection_func, bot_instance):
    """Инициализация модуля с зависимостями"""
    global broadcast_model, broadcast_service
    broadcast_model = BroadcastModel(db_connection_func)
    broadcast_service = BroadcastService(bot_instance, broadcast_model)

@broadcast_bp.route('/')
@login_required
def broadcast_list():
    """Список всех рассылок"""
    try:
        broadcasts = broadcast_model.get_all_broadcasts()
        return render_template('broadcast/list.html', broadcasts=broadcasts)
    except Exception as e:
        flash(f'Ошибка при загрузке рассылок: {str(e)}', 'danger')
        return render_template('broadcast/list.html', broadcasts=[])

@broadcast_bp.route('/create')
@login_required
def broadcast_create():
    """Страница создания рассылки"""
    return render_template('broadcast/create.html')

@broadcast_bp.route('/create', methods=['POST'])
@login_required
def broadcast_create_post():
    """Создание новой рассылки"""
    try:
        data = request.get_json()
        
        # Проверяем тип рассылки
        if data.get('type') == 'single':
            # Обычная рассылка
            broadcast_id = broadcast_model.create_broadcast(
                name=data['name'],
                message=data['message'],
                audience_type=data['audience']
            )
        else:
            # Сценарий
            broadcast_id = broadcast_service.create_scenario(
                name=data['name'],
                audience_type=data['audience'],
                scenario_type=data['scenario']
            )
        
        return jsonify({'success': True, 'broadcast_id': broadcast_id})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@broadcast_bp.route('/<int:broadcast_id>/stats')
@login_required
def broadcast_stats(broadcast_id):
    """Статистика рассылки"""
    try:
        stats = broadcast_model.get_broadcast_stats(broadcast_id)
        if not stats:
            flash('Рассылка не найдена', 'danger')
            return redirect(url_for('broadcast.broadcast_list'))
        
        return render_template('broadcast/stats.html', broadcast=stats)
    except Exception as e:
        flash(f'Ошибка: {str(e)}', 'danger')
        return redirect(url_for('broadcast.broadcast_list'))

@broadcast_bp.route('/<int:broadcast_id>/send', methods=['POST'])
@login_required
async def broadcast_send(broadcast_id):
    """Отправить рассылку"""
    try:
        test_mode = request.json.get('test_mode', False)
        result = await broadcast_service.send_broadcast(broadcast_id, test_mode)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@broadcast_bp.route('/<int:broadcast_id>/delete', methods=['POST'])
@login_required
def broadcast_delete(broadcast_id):
    """Удалить рассылку"""
    try:
        if broadcast_model.delete_broadcast(broadcast_id):
            flash('Рассылка удалена', 'success')
        else:
            flash('Невозможно удалить рассылку', 'danger')
    except Exception as e:
        flash(f'Ошибка: {str(e)}', 'danger')
    
    return redirect(url_for('broadcast.broadcast_list'))

@broadcast_bp.route('/preview', methods=['POST'])
@login_required
def broadcast_preview():
    """Предпросмотр аудитории"""
    try:
        audience_type = request.json.get('audience')
        count = broadcast_model.get_audience_preview(audience_type)
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
