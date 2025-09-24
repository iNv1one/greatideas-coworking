#!/bin/bash
# Скрипт для развертывания GreatIdeas на сервере

echo "🚀 Начинаем развертывание GreatIdeas..."

# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем необходимые пакеты
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib git

# Создаем пользователя для приложения
sudo useradd --system --home /var/www/greatideas --shell /bin/bash greatideas

# Создаем директории
sudo mkdir -p /var/www/greatideas
sudo mkdir -p /var/log/greatideas
sudo chown greatideas:greatideas /var/www/greatideas
sudo chown greatideas:greatideas /var/log/greatideas

# Переходим в директорию проекта
cd /var/www/greatideas

# Клонируем проект (замените на ваш репозиторий)
sudo -u greatideas git clone https://github.com/yourusername/greatideas.git .

# Создаем виртуальное окружение
sudo -u greatideas python3 -m venv venv

# Активируем окружение и устанавливаем зависимости
sudo -u greatideas bash -c "source venv/bin/activate && pip install -r requirements.txt"

# Настраиваем PostgreSQL
sudo -u postgres psql -c "CREATE DATABASE greatideas_db;"
sudo -u postgres psql -c "CREATE USER greatideas_user WITH PASSWORD 'your_secure_password_here';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE greatideas_db TO greatideas_user;"

# Применяем миграции
sudo -u greatideas bash -c "source venv/bin/activate && python manage.py migrate"

# Собираем статические файлы
sudo -u greatideas bash -c "source venv/bin/activate && python manage.py collectstatic --noinput"

# Настраиваем systemd сервисы для ботов
echo "🤖 Настраиваем Telegram ботов..."

# Копируем сервисы
sudo cp telegram-bot.service /etc/systemd/system/
sudo cp staff-bot.service /etc/systemd/system/
sudo cp gunicorn.service /etc/systemd/system/
sudo cp gunicorn.socket /etc/systemd/system/

# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем сервисы
sudo systemctl enable gunicorn.socket
sudo systemctl enable telegram-bot.service
sudo systemctl enable staff-bot.service

echo "✅ Основная настройка завершена!"
echo "🔧 Теперь настройте переменные окружения в .env"
echo "🤖 Запустите ботов командами:"
echo "   sudo systemctl start telegram-bot"
echo "   sudo systemctl start staff-bot"
echo "🌐 Настройте Nginx и запустите веб-сервер"