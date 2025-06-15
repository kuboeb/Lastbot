from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import asyncio
import logging
from datetime import datetime

from config import config
from database import db_manager, BotUser, Application, BotSetting, OperatorMessage
from api.auth import require_api_key, require_internal_key
from utils.conversions import verify_webhook_signature

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)

@api_bp.route('/send_message', methods=['POST'])
@require_api_key
@limiter.limit("100 per hour")
def send_single_message():
    """Отправка одного сообщения пользователю"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    identifier_type = data.get('identifier_type')
    identifier = data.get('identifier')
    message_text = data.get('message')
    operator_id = data.get('operator_id', 'unknown')
    
    if not all([identifier_type, identifier, message_text]):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Здесь должна быть логика отправки через бота
    # TODO: Implement bot message sending
    
    # Сохраняем в БД
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def save_message():
            async with db_manager.get_session() as session:
                operator_msg = OperatorMessage(
                    phone=identifier if identifier_type == 'phone' else None,
                    user_id=int(identifier) if identifier_type == 'user_id' else None,
                    message=message_text,
                    operator_id=operator_id,
                    delivered=False
                )
                session.add(operator_msg)
                await session.commit()
                return operator_msg.id
        
        message_id = loop.run_until_complete(save_message())
        
        return jsonify({
            "status": "success",
            "message_id": message_id,
            "identifier": identifier
        })
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return jsonify({"error": "Failed to send message"}), 500

@api_bp.route('/send_bulk_messages', methods=['POST'])
@require_api_key
@limiter.limit("50 per hour")
def send_bulk_messages():
    """Массовая рассылка сообщений"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    identifier_type = data.get('identifier_type')
    identifiers = data.get('identifiers', [])
    message_text = data.get('message')
    operator_id = data.get('operator_id', 'unknown')
    
    if not all([identifier_type, identifiers, message_text]):
        return jsonify({"error": "Missing required fields"}), 400
    
    if len(identifiers) > 500:
        return jsonify({"error": "Too many recipients. Maximum 500 allowed"}), 400
    
    # TODO: Implement bulk sending logic
    
    sent = []
    not_found = []
    
    # Заглушка для демонстрации
    for identifier in identifiers:
        if identifier.startswith('+'):  # Простая проверка для примера
            sent.append({"identifier": identifier, "status": "sent"})
        else:
            not_found.append(identifier)
    
    return jsonify({
        "sent": len(sent),
        "not_found": len(not_found),
        "not_found_identifiers": not_found,
        "details": sent[:100]  # Первые 100 для примера
    })

@api_bp.route('/bot/status', methods=['GET'])
@require_internal_key
def bot_status():
    """Получение статуса бота"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def get_status():
            async with db_manager.get_session() as session:
                # Получаем настройки бота
                bot_enabled = await session.query(BotSetting).filter_by(
                    key='bot_enabled'
                ).first()
                
                bot_start_time = await session.query(BotSetting).filter_by(
                    key='bot_start_time'
                ).first()
                
                # Считаем последнюю активность
                last_user = await session.query(BotUser).order_by(
                    BotUser.last_activity.desc()
                ).first()
                
                return {
                    "enabled": bot_enabled.value == 'true' if bot_enabled else True,
                    "start_time": bot_start_time.value if bot_start_time else None,
                    "last_activity": last_user.last_activity.isoformat() if last_user else None
                }
        
        status = loop.run_until_complete(get_status())
        
        # Вычисляем uptime
        if status['start_time']:
            start = datetime.fromisoformat(status['start_time'])
            uptime = datetime.now() - start
            hours, remainder = divmod(int(uptime.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            days, hours = divmod(hours, 24)
            
            uptime_str = f"{days}d {hours}h {minutes}m"
        else:
            uptime_str = "unknown"
        
        return jsonify({
            "enabled": status['enabled'],
            "uptime": uptime_str,
            "last_message": status['last_activity'],
            "version": "1.0.0"
        })
        
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        return jsonify({"error": "Failed to get status"}), 500

@api_bp.route('/bot/toggle', methods=['POST'])
@require_internal_key
def toggle_bot():
    """Включение/выключение бота"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def toggle():
            async with db_manager.get_session() as session:
                bot_enabled = await session.query(BotSetting).filter_by(
                    key='bot_enabled'
                ).first()
                
                if bot_enabled:
                    new_status = 'false' if bot_enabled.value == 'true' else 'true'
                    bot_enabled.value = new_status
                else:
                    new_setting = BotSetting(key='bot_enabled', value='true')
                    session.add(new_setting)
                    new_status = 'true'
                
                await session.commit()
                return new_status == 'true'
        
        enabled = loop.run_until_complete(toggle())
        
        return jsonify({
            "enabled": enabled,
            "message": f"Bot {'enabled' if enabled else 'disabled'} successfully"
        })
        
    except Exception as e:
        logger.error(f"Error toggling bot: {e}")
        return jsonify({"error": "Failed to toggle bot"}), 500

@api_bp.route('/stats/funnel', methods=['GET'])
@require_internal_key
def get_funnel_stats():
    """Получение статистики воронки"""
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def get_stats():
            async with db_manager.get_session() as session:
                from sqlalchemy import func, and_
                from database import UserAction
                
                # Базовый запрос
                query = session.query(
                    UserAction.action,
                    func.count(func.distinct(UserAction.user_id)).label('count')
                ).group_by(UserAction.action)
                
                # Фильтры по датам
                if date_from:
                    query = query.filter(UserAction.created_at >= date_from)
                if date_to:
                    query = query.filter(UserAction.created_at <= date_to)
                
                results = await session.execute(query)
                stats = {row.action: row.count for row in results}
                
                return {
                    "started": stats.get('start', 0),
                    "entered_name": stats.get('enter_name', 0),
                    "entered_country": stats.get('enter_country', 0),
                    "entered_phone": stats.get('enter_phone', 0),
                    "entered_time": stats.get('enter_time', 0),
                    "completed": stats.get('complete_registration', 0)
                }
        
        stats = loop.run_until_complete(get_stats())
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting funnel stats: {e}")
        return jsonify({"error": "Failed to get stats"}), 500

@api_bp.route('/webhook/<int:integration_id>', methods=['POST'])
def handle_webhook(integration_id):
    """Обработка входящих webhook от CRM"""
    # Проверяем подпись
    signature = request.headers.get('X-Webhook-Signature')
    if not signature:
        return jsonify({"error": "Missing signature"}), 401
    
    if not verify_webhook_signature(
        signature,
        request.data.decode('utf-8'),
        config.WEBHOOK_SIGNATURE_KEY
    ):
        return jsonify({"error": "Invalid signature"}), 401
    
    # Обрабатываем данные
    data = request.get_json()
    logger.info(f"Received webhook for integration {integration_id}: {data}")
    
    # TODO: Implement webhook processing logic
    
    return jsonify({"status": "received"}), 200
