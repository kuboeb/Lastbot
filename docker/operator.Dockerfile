FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование файла зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание директории для логов
RUN mkdir -p logs

# Создание непривилегированного пользователя
RUN useradd -m -u 1000 operatoruser && chown -R operatoruser:operatoruser /app
USER operatoruser

# Экспорт порта
EXPOSE 5000

# Команда по умолчанию
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "operator_panel.app:app"]
