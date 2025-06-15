from functools import wraps
from flask import request, jsonify
import logging

from config import config

logger = logging.getLogger(__name__)

def verify_api_key(api_key: str) -> bool:
    """Проверка API ключа оператора"""
    return api_key == config.OPERATOR_API_KEY

def verify_internal_key(api_key: str) -> bool:
    """Проверка внутреннего API ключа"""
    return api_key == config.INTERNAL_API_KEY

def require_api_key(f):
    """Декоратор для проверки API ключа оператора"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            logger.warning("Missing API key in request")
            return jsonify({"error": "Missing API key"}), 401
        
        if not verify_api_key(api_key):
            logger.warning(f"Invalid API key attempt: {api_key[:10]}...")
            return jsonify({"error": "Invalid API key"}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_internal_key(f):
    """Декоратор для проверки внутреннего API ключа"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            logger.warning("Missing internal API key in request")
            return jsonify({"error": "Missing API key"}), 401
        
        if not verify_internal_key(api_key):
            logger.warning(f"Invalid internal API key attempt: {api_key[:10]}...")
            return jsonify({"error": "Invalid API key"}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_client_ip(request) -> str:
    """Получение реального IP клиента"""
    if request.headers.get('X-Forwarded-For'):
        # За прокси/nginx
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    else:
        ip = request.remote_addr
    
    return ip
