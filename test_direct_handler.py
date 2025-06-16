import asyncio
import logging
from handlers.facebook_utils import save_user_fbclid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Тест прямого вызова функции сохранения fbclid
def test_save_fbclid():
    user_id = 7825279349  # Ваш user_id из логов
    fbclid = "IwAR_DIRECT_TEST_12345"
    raw_params = "src_test__fbclid_IwAR_DIRECT_TEST_12345"
    
    print(f"Тестируем сохранение fbclid для user {user_id}")
    result = save_user_fbclid(user_id, fbclid, raw_params)
    print(f"Результат: {result}")

if __name__ == "__main__":
    test_save_fbclid()
