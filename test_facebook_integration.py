import asyncio
import sys
sys.path.append('/home/Lastbot/admin_panel')

from facebook_module.models import save_user_click, get_user_click_id

async def test():
    # Тест сохранения click_id
    user_id = 123456789
    click_id = "IwAR1234567890test"
    
    # Сохраняем
    result = save_user_click(user_id, click_id, 'fbclid')
    print(f"Save result: {result}")
    
    # Получаем обратно
    saved_click_id = get_user_click_id(user_id, 'fbclid')
    print(f"Retrieved click_id: {saved_click_id}")
    
    if saved_click_id == click_id:
        print("✅ Test passed!")
    else:
        print("❌ Test failed!")

if __name__ == "__main__":
    asyncio.run(test())
