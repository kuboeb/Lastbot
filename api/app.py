from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import logging
import hmac
import hashlib
import time
from functools import wraps

from config import config
from database import db_manager
from api.routes import api_bp
from api.auth import verify_api_key

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создание Flask приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = config.FLASK_SECRET_KEY

# Настройка CORS
CORS(app, origins=[
    f"http://{config.SERVER_IP}:8000",
    f"http://{config.SERVER_IP}:8001",
    "http://localhost:8000",
    "http://localhost:8001"
])

# Настройка rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per hour"]
)

# Регистрация blueprints
app.register_blueprint(api_bp, url_prefix='/api')

@app.before_first_request
async def startup():
    """Инициализация при первом запросе"""
    await db_manager.connect()
    logger.info("API server started")

@app.teardown_appcontext
async def shutdown(error=None):
    """Очистка ресурсов"""
    if error:
        logger.error(f"Application error: {error}")

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка состояния сервиса"""
    return jsonify({
        "status": "healthy",
        "service": "crypto_bot_api",
        "timestamp": time.time()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({"error": "Rate limit exceeded"}), 429

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=config.BOT_API_PORT,
        debug=False
    )
