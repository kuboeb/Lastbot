#!/usr/bin/env python3
import asyncio
import asyncpg
from datetime import datetime
import os
import sys
sys.path.append('/home/Lastbot')
from config import Config

async def test_conversion():
    # Подключаемся к БД
    conn = await asyncpg.connect(Config.DATABASE_URL)
    
    print("=== ТЕСТ КОНВЕРСИЙ ===\n")
    
    # 1. Получаем тестовый источник
    source = await conn.fetchrow("SELECT * FROM traffic_sources LIMIT 1")
    if not source:
        print("❌ Нет источников трафика. Создайте через админку.")
        return
    
    print(f"✅ Используем источник: {source['name']} ({source['platform']})")
    print(f"   Ссылка: {source['link']}")
    print(f"   Код: {source['source_code']}\n")
    
    # 2. Симулируем переход пользователя
    test_user_id = 9999999999  # Тестовый user_id
    test_click_id = "test_fbclid_IwAR0123456789"
    
    print("2. Симулируем переход по ссылке с fbclid...")
    
    # Записываем клик
    await conn.execute("""
        INSERT INTO tracking_events (source_id, user_id, event_type, click_id)
        VALUES ($1, $2, 'click', $3)
    """, source['id'], test_user_id, test_click_id)
    
    # Сохраняем click_id
    await conn.execute("""
        INSERT INTO user_click_ids (user_id, source_id, click_id, click_type)
        VALUES ($1, $2, $3, 'fbclid')
        ON CONFLICT (user_id, click_type) DO UPDATE 
        SET click_id = EXCLUDED.click_id
    """, test_user_id, source['id'], test_click_id)
    
    print("   ✅ Click event записан")
    print(f"   ✅ fbclid сохранен: {test_click_id}\n")
    
    # 3. Симулируем start
    print("3. Симулируем нажатие /start...")
    await conn.execute("""
        INSERT INTO tracking_events (source_id, user_id, event_type)
        VALUES ($1, $2, 'start')
    """, source['id'], test_user_id)
    print("   ✅ Start event записан\n")
    
    # 4. Симулируем заявку (lead)
    print("4. Симулируем отправку заявки...")
    
    # Создаем тестовую заявку
    app_id = await conn.fetchval("""
        INSERT INTO applications (user_id, full_name, country, phone, preferred_time, source_id)
        VALUES ($1, 'Тест Тестов', 'Испания', '+34123456789', '12:00-15:00', $2)
        RETURNING id
    """, test_user_id, source['id'])
    
    # Записываем lead event
    await conn.execute("""
        INSERT INTO tracking_events (source_id, user_id, event_type)
        VALUES ($1, $2, 'lead')
    """, source['id'], test_user_id)
    
    # Создаем запись о конверсии
    await conn.execute("""
        INSERT INTO conversion_logs (source_id, user_id, application_id, platform, status, request_data)
        VALUES ($1, $2, $3, $4, 'test', $5)
    """, source['id'], test_user_id, app_id, source['platform'], 
        '{"test": true, "timestamp": "' + datetime.now().isoformat() + '"}')
    
    print("   ✅ Lead event записан")
    print(f"   ✅ Заявка создана: ID {app_id}")
    print("   ✅ Conversion log создан\n")
    
    # 5. Проверяем статистику
    print("5. ПРОВЕРКА СТАТИСТИКИ:")
    
    stats = await conn.fetchrow("""
        SELECT 
            COUNT(CASE WHEN event_type = 'click' THEN 1 END) as clicks,
            COUNT(CASE WHEN event_type = 'start' THEN 1 END) as starts,
            COUNT(CASE WHEN event_type = 'lead' THEN 1 END) as leads
        FROM tracking_events 
        WHERE source_id = $1 AND user_id = $2
    """, source['id'], test_user_id)
    
    print(f"   Клики: {stats['clicks']}")
    print(f"   Старты: {stats['starts']}")
    print(f"   Лиды: {stats['leads']}")
    print(f"   Конверсия: {stats['leads']/stats['clicks']*100:.1f}%\n")
    
    # 6. Проверяем click_id
    click_id_data = await conn.fetchrow("""
        SELECT * FROM user_click_ids 
        WHERE user_id = $1 AND source_id = $2
    """, test_user_id, source['id'])
    
    if click_id_data:
        print(f"6. СОХРАНЕННЫЙ CLICK_ID:")
        print(f"   Тип: {click_id_data['click_type']}")
        print(f"   ID: {click_id_data['click_id']}\n")
    
    # 7. Очистка тестовых данных
    print("7. Очистка тестовых данных...")
    await conn.execute("DELETE FROM tracking_events WHERE user_id = $1", test_user_id)
    await conn.execute("DELETE FROM user_click_ids WHERE user_id = $1", test_user_id)
    await conn.execute("DELETE FROM conversion_logs WHERE user_id = $1", test_user_id)
    await conn.execute("DELETE FROM applications WHERE user_id = $1", test_user_id)
    print("   ✅ Тестовые данные удалены\n")
    
    await conn.close()
    
    print("=== ТЕСТ ЗАВЕРШЕН ===")
    print("\nТеперь проверьте в админке:")
    print("1. Перейдите на страницу источника")
    print("2. Посмотрите вкладку 'Конверсии'")
    print("3. Посмотрите вкладку 'Click IDs'")

if __name__ == "__main__":
    asyncio.run(test_conversion())
