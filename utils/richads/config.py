"""
Конфигурация для RichAds
Изолированный модуль - не влияет на другие интеграции
"""

RICHADS_CONFIG = {
    'postback_url': 'https://us.ahows.co/log',
    'platform_name': 'richads',
    'click_type': 'richads_click',
    'success_statuses': [200, 202],
    'timeout': 10,
    'max_retries': 3
}

# Форматы параметров в ссылке
LINK_PATTERNS = {
    'minimal': 'src_{code}__{click_id}',
    'with_campaign': 'src_{code}__{click_id}__{campaign}'
}
