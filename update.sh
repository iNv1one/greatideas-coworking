#!/bin/bash
# Скрипт для обновления GreatIdeas на сервере

echo "🔄 Начинаем обновление GreatIdeas..."

# Переходим в директорию проекта
cd /home/www-data/greatideas

# Останавливаем сервисы
echo "⏹️ Останавливаем сервисы..."
sudo systemctl stop telegram-bot
sudo systemctl stop staff-bot
sudo systemctl stop gunicorn

# Делаем backup базы данных
echo "💾 Создаем backup базы данных..."
sudo -u postgres pg_dump greatideas_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Получаем обновления из git
echo "📥 Получаем обновления..."
sudo -u www-data git pull origin main

# Обновляем зависимости
echo "📦 Обновляем зависимости..."
sudo -u www-data bash -c "source venv/bin/activate && pip install -r requirements.txt"

# Применяем миграции
echo "🔄 Применяем миграции..."
sudo -u www-data bash -c "source venv/bin/activate && python manage.py migrate"

# Собираем статику
echo "🎨 Собираем статические файлы..."
sudo -u www-data bash -c "source venv/bin/activate && python manage.py collectstatic --noinput"

# Обновляем сервисы systemd
echo "🔧 Обновляем сервисы..."
sudo cp telegram-bot.service /etc/systemd/system/
sudo cp staff-bot.service /etc/systemd/system/
sudo systemctl daemon-reload

# Запускаем сервисы
echo "▶️ Запускаем сервисы..."
sudo systemctl start gunicorn
sudo systemctl start telegram-bot
sudo systemctl start staff-bot

# Проверяем статус
echo "🔍 Проверяем статус сервисов..."
sudo systemctl status gunicorn --no-pager -l
sudo systemctl status telegram-bot --no-pager -l
sudo systemctl status staff-bot --no-pager -l

echo "✅ Обновление завершено!"
echo "🤖 Боты запущены и работают"
echo "🌐 Веб-сервер перезапущен"