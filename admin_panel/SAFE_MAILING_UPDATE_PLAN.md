# План безопасного обновления системы рассылок

## Шаг 1: Создание новых роутов БЕЗ удаления старых
- Добавить роуты /mailing/* параллельно с /broadcast
- Протестировать новые роуты

## Шаг 2: Создание новых шаблонов
- Создать templates/mailing/* 
- Не трогать старые шаблоны

## Шаг 3: Обновление меню
- Добавить новый пункт "Рассылки 2.0"
- Оставить старый пункт "Рассылка"

## Шаг 4: Тестирование
- Проверить работу обеих систем
- Убедиться в стабильности

## Шаг 5: Миграция
- Перенести данные
- Отключить старую систему
