#!/bin/bash

# Запуск Redis и Postgres в Docker
docker-compose up -d

# Активация виртуального окружения (если нужно)
# source venv/bin/activate  # Для Linux/Mac
source venv/Scripts/activate  # Для Windows

# Установка зависимостей
pip install -r requirements.txt

# Запуск приложения
python -m app.main

# Остановка контейнеров при завершении
docker-compose down
