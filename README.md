# GreatIdeas - Telegram Coworking Bot

Сеть уютных кафе с возможностью заказа через Telegram Web App и оплатой через Telegram Payments.

## Особенности

- 🏪 Каталог кафе с уникальными меню
- 🛒 Корзина с управлением количеством
- 📱 Telegram Web App интеграция
- 💳 Оплата через Telegram Payments (ЮKassa)
- 🤖 Telegram бот для уведомлений
- 🎨 Адаптивный дизайн

## Технологии

- **Backend**: Django 5.2.6, Python 3.x
- **Frontend**: Bootstrap 5.3.0, Vanilla JS
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Bot**: python-telegram-bot
- **Payments**: Telegram Payments API, ЮKassa
- **Deploy**: Nginx, Gunicorn, Ubuntu Server

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/YOUR-USERNAME/greatideas-coworking.git
cd greatideas-coworking
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройте .env файл:
```env
DEBUG=True
SECRET_KEY=your-secret-key
TELEGRAM_BOT_TOKEN=your-bot-token
PAYMENT_PROVIDER_TOKEN=your-payment-token
ALLOWED_HOSTS=localhost,127.0.0.1
```

5. Примените миграции:
```bash
python manage.py migrate
python manage.py collectstatic
```

6. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

7. Запустите сервер:
```bash
python manage.py runserver
```

## Деплоймент

См. `SERVER_DEPLOYMENT.md` для подробных инструкций по развертыванию на сервере.

## Лицензия

MIT License