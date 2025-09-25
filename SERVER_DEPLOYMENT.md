# Развертывание Django проекта на сервере 89.110.123.93

## 🏗️ Архитектура развертывания

### Что мы строим:
```
Интернет → Nginx (веб-сервер) → Gunicorn (WSGI сервер) → Django (приложение)
```

### Роли компонентов:

**🌐 Nginx** - Веб-сервер (фронтенд)
- Принимает HTTP запросы из интернета на порт 80
- Отдает статические файлы (CSS, JS, изображения) напрямую
- Проксирует динамические запросы к Django через Gunicorn
- Обеспечивает безопасность, кэширование, сжатие

**🔧 Gunicorn** - WSGI сервер (мост)
- Запускает несколько worker процессов Django
- Принимает запросы от Nginx на внутреннем порту 8000
- Управляет жизненным циклом Django процессов
- Обеспечивает производительность и стабильность

**🐍 Django** - Веб-приложение (бэкенд)
- Ваш код на Python
- Обрабатывает бизнес-логику
- Работает с базой данных
- Генерирует HTML ответы

### Зачем такая схема?
1. **Производительность**: Nginx быстро отдает статику
2. **Масштабируемость**: Gunicorn запускает несколько Django процессов
3. **Надежность**: Если один процесс Django упадет, остальные продолжат работать
4. **Безопасность**: Nginx защищает от многих атак

## Шаг 1: Подготовка проекта к загрузке

**🎯 Цель:** Упаковать ваш Django проект для передачи на сервер

**💡 Что происходит:** Создаем архив всех файлов проекта, чтобы одной командой загрузить их на удаленный сервер

### 1.1 Создание архива проекта (на вашем ПК)
```powershell
cd C:\gibot
Compress-Archive -Path "greatideas" -DestinationPath "greatideas.zip" -Force
```

### 1.2 Удаление правила файрвола (если создавали)
```powershell
# Запустите PowerShell от имени администратора
netsh advfirewall firewall delete rule name="Django Server"
```

## Шаг 2: Подключение к серверу

**🎯 Цель:** Получить доступ к удаленному серверу и подготовить его к работе

**💡 Что происходит:** 
- SSH (Secure Shell) - зашифрованное соединение с сервером
- Обновляем пакеты Ubuntu для безопасности
- Устанавливаем необходимые компоненты

### 2.1 SSH подключение
```bash
ssh root@89.110.123.93
```

### 2.2 Обновление системы
```bash
apt update && apt upgrade -y
```

### 2.3 Установка необходимых пакетов
```bash
apt install python3 python3-pip python3-venv nginx git unzip -y
```

**🔧 Что устанавливаем:**
- `python3` - интерпретатор Python для запуска Django
- `python3-pip` - менеджер пакетов Python 
- `python3-venv` - создание виртуальных окружений
- `nginx` - веб-сервер для проксирования запросов
- `git` - система контроля версий (на случай обновлений)
- `unzip` - для распаковки архива проекта

## Шаг 3: Загрузка проекта на сервер

**🎯 Цель:** Перенести ваш код с локального ПК на удаленный сервер

**💡 Что происходит:**
- SCP (Secure Copy) - зашифрованная передача файлов через SSH
- Размещаем проект в `/var/www/` - стандартная папка для веб-сайтов
- Настраиваем права доступа для веб-сервера

### 3.1 Загрузка архива (с вашего ПК)
```powershell
scp greatideas.zip root@89.110.123.93:/var/www/
```

### 3.2 Распаковка на сервере
```bash
cd /var/www
unzip greatideas.zip
chown -R www-data:www-data greatideas
```

**📁 Структура папок:**
- `/var/www/` - стандартное место для веб-сайтов в Linux
- `chown www-data:www-data` - даем права пользователю веб-сервера
- `www-data` - специальный пользователь для запуска веб-служб

## Шаг 4: Настройка Python окружения

**🎯 Цель:** Создать изолированную среду для Python пакетов вашего проекта

**💡 Зачем виртуальное окружение:**
- Изоляция зависимостей (пакеты проекта не конфликтуют с системными)
- Контроль версий библиотек
- Безопасность (можно удалить без вреда системе)
- Воспроизводимость (одинаковые версии на разных серверах)

### 4.1 Создание виртуального окружения
```bash
cd /var/www/greatideas
python3 -m venv venv
source venv/bin/activate
```

### 4.2 Установка зависимостей
```bash
pip install django pillow python-decouple gunicorn djangorestframework
```

**📦 Устанавливаемые пакеты:**
- `django` - основной фреймворк для веб-разработки
- `pillow` - обработка изображений (для ImageField в моделях)
- `python-decouple` - работа с переменными окружения (.env файлы)
- `gunicorn` - WSGI HTTP сервер для продакшена
- `djangorestframework` - API фреймворк (REST API)

### 4.3 Создание файла .env для продакшена
```bash
nano .env
```

Содержимое .env:
```
DEBUG=False
SECRET_KEY=your-very-long-secret-key-for-production-change-this
ALLOWED_HOSTS=localhost,127.0.0.1,89.110.123.93,coworking.greatideas.ru,www.coworking.greatideas.ru
```

**🔐 Переменные окружения:**
- `DEBUG=False` - отключает отладочную информацию (важно для безопасности!)
- `SECRET_KEY` - криптографический ключ Django (должен быть уникальным!)
- `ALLOWED_HOSTS` - список разрешенных доменов/IP (защита от HTTP Host header атак)

## Шаг 5: Настройка Django

**🎯 Цель:** Подготовить базу данных и статические файлы для работы в продакшене

**💡 Что происходит:**
- Миграции создают/обновляют структуру базы данных
- Collectstatic собирает все CSS/JS/изображения в одну папку для Nginx
- Суперпользователь нужен для доступа к админ-панели Django

### 5.1 Применение миграций и сбор статики
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

**🔧 Что делают команды:**
- `migrate` - применяет изменения к базе данных (создает таблицы)
- `collectstatic` - копирует все статические файлы в STATIC_ROOT
- `createsuperuser` - создает администратора для /admin/ панели

### 5.2 Тестовый запуск
```bash
python manage.py runserver 0.0.0.0:8000
# Проверьте доступность: http://89.110.123.93:8000
# Остановите: Ctrl+C
```

## Шаг 6: Настройка Gunicorn

**🎯 Цель:** Настроить WSGI сервер для запуска Django в продакшене

**💡 Что такое Gunicorn:**
- **WSGI** (Web Server Gateway Interface) - стандарт взаимодействия веб-серверов и Python приложений
- **Gunicorn** = Green Unicorn - WSGI HTTP сервер для UNIX
- Запускает несколько worker процессов Django для обработки запросов параллельно
- Более стабильный и производительный чем встроенный runserver Django

**⚡ Преимущества:**
- Автоматический перезапуск упавших процессов
- Балансировка нагрузки между worker'ами  
- Graceful restart (перезапуск без потери соединений)
- Мониторинг и логирование

### 6.1 Создание конфигурации Gunicorn
```bash
nano gunicorn.conf.py
```

Содержимое:
```python
bind = "127.0.0.1:8000"
workers = 3
user = "www-data"
group = "www-data"
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
```

### 6.2 Создание systemd сервиса
```bash
nano /etc/systemd/system/greatideas.service
```

Содержимое:
```ini
[Unit]
Description=Gunicorn instance to serve GreatIdeas
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/var/www/greatideas
Environment="PATH=/var/www/greatideas/venv/bin"
ExecStart=/var/www/greatideas/venv/bin/gunicorn greatideas.wsgi:application --bind 127.0.0.1:8000 --workers 3
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

**🔧 Что такое systemd сервис:**
- **systemd** - система инициализации Linux (запускает службы при загрузке)
- Автоматический запуск Gunicorn при старте сервера
- Автоматический перезапуск при сбоях
- Логирование через journalctl
- Управление через systemctl (start/stop/restart)

**⚙️ Параметры конфигурации:**
- `--bind 127.0.0.1:8000` - слушает только внутренние подключения (от Nginx)
- `--workers 3` - запускает 3 процесса Django (обычно = количество CPU ядер)
- `Restart=on-failure` - перезапуск при крашах

### 6.3 Запуск сервиса
```bash
systemctl daemon-reload
systemctl start greatideas
systemctl enable greatideas
systemctl status greatideas
```

## Шаг 7: Настройка Nginx

**🎯 Цель:** Настроить веб-сервер для обработки HTTP запросов из интернета

**💡 Что такое Nginx:**
- **Веб-сервер** и **обратный прокси** (reverse proxy)
- Принимает HTTP запросы из интернета на порт 80/443
- Статические файлы отдает сам (быстро)
- Динамические запросы проксирует к Gunicorn
- Обеспечивает SSL, сжатие, кэширование, защиту от атак

**🚀 Архитектура запроса:**
```
1. Пользователь → http://coworking.greatideas.ru/cafe/1/
2. Nginx получает запрос на порт 80
3. Проверяет: это статический файл? Если да - отдает сам
4. Если нет - проксирует к Gunicorn на 127.0.0.1:8000
5. Gunicorn запускает Django код
6. Django возвращает HTML
7. Nginx отправляет ответ пользователю
```

### 7.1 Создание конфигурации сайта
```bash
nano /etc/nginx/sites-available/greatideas
```

Содержимое:
```nginx
server {
    listen 80;
    server_name 89.110.123.93 coworking.greatideas.ru www.coworking.greatideas.ru;
    
    location /static/ {
        alias /var/www/greatideas/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /var/www/greatideas/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**🔧 Разбор конфигурации:**
- `listen 80` - слушает HTTP запросы на порту 80
- `server_name` - список доменов, которые обслуживает этот блок
- `location /static/` - статические файлы (CSS, JS) отдает напрямую с диска
- `location /media/` - загруженные файлы (изображения) отдает напрямую
- `location /` - все остальные запросы проксирует к Django
- `expires 30d` - кэширование статики на 30 дней в браузере
- `proxy_set_header` - передает информацию о клиенте в Django

### 7.2 Активация сайта
```bash
ln -s /etc/nginx/sites-available/greatideas /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

**📁 Структура конфигураций Nginx:**
- `/etc/nginx/sites-available/` - все доступные конфигурации сайтов
- `/etc/nginx/sites-enabled/` - активные сайты (символические ссылки)
- `nginx -t` - проверка синтаксиса конфигурации
- `systemctl restart nginx` - перезапуск для применения изменений

## Шаг 8: Настройка DNS (reg.ru)

**🎯 Цель:** Привязать домен coworking.greatideas.ru к IP адресу вашего сервера

**💡 Что такое DNS:**
- **DNS** (Domain Name System) - система доменных имен
- Переводит человекочитаемые домены в IP адреса
- **A-запись** - связывает домен с IPv4 адресом
- **CNAME-запись** - создает псевдоним (алиас) для домена
- **TTL** (Time To Live) - время кэширования записи в секундах

**🌐 Как работает:**
```
1. Пользователь вводит coworking.greatideas.ru
2. Браузер спрашивает DNS сервер: "Какой IP у этого домена?"
3. DNS сервер отвечает: "89.110.123.93"
4. Браузер подключается к вашему серверу
5. Nginx на сервере получает запрос и обрабатывает его
```

### 8.1 Войдите в панель управления reg.ru
1. Перейдите в управление доменом `greatideas.ru`
2. Найдите раздел "DNS-записи"

### 8.2 Добавьте A-запись
```
Имя: coworking
Тип: A
Значение: 89.110.123.93
TTL: 3600
```

### 8.3 Добавьте CNAME-запись (опционально)
```
Имя: www.coworking
Тип: CNAME
Значение: coworking.greatideas.ru
TTL: 3600
```

**📋 Объяснение записей:**
- **A-запись** `coworking` → создает `coworking.greatideas.ru`
- **CNAME-запись** `www.coworking` → создает `www.coworking.greatideas.ru`
- **TTL: 3600** - запись кэшируется на 1 час (3600 секунд)
- **Время распространения:** до 24 часов по всему миру

### 8.4 Проверка распространения DNS

**🔍 Способы проверки:**

**1. Онлайн сервисы (самый простой):**
- Сеть уютных кафе с отличной едой и атмосферой - введите `coworking.greatideas.ru`
- https://whatsmydns.net - проверка по всему миру
- https://dns.google - Google DNS lookup

**2. Командная строка (на вашем ПК):**
```powershell
# Windows PowerShell
nslookup coworking.greatideas.ru
# Если возвращает 89.110.123.93 - DNS работает!

# Проверка через разные DNS серверы
nslookup coworking.greatideas.ru 8.8.8.8
nslookup coworking.greatideas.ru 1.1.1.1
```

**3. Проверка в браузере:**
```
http://coworking.greatideas.ru
# Если открывается ваш сайт - все работает!
```

**📊 Этапы распространения DNS:**
```
🕐 0-15 минут: reg.ru обновляет свои серверы
🕐 15-60 минут: распространение по России  
🕐 1-6 часов: распространение по СНГ
🕐 6-24 часа: полное распространение по миру
```

**⚡ Ускорение проверки:**
- Очистите DNS кэш: `ipconfig /flushdns` (Windows)
- Используйте режим инкогнито в браузере
- Проверяйте через мобильный интернет (другой провайдер)

## Шаг 9: Настройка безопасности

**🎯 Цель:** Защитить сервер от атак и обеспечить безопасную передачу данных

**🔒 Что настраиваем:**
- **UFW** (Uncomplicated Firewall) - простой файрвол для Ubuntu
- **SSL сертификат** - шифрование HTTPS соединений
- **Let's Encrypt** - бесплатные SSL сертификаты

### 9.1 Настройка файрвола UFW
```bash
ufw enable
ufw allow ssh
ufw allow 'Nginx Full'
ufw status
```

**🛡️ Правила файрвола:**
- `ufw enable` - включает файрвол
- `ufw allow ssh` - разрешает SSH подключения (порт 22)
- `ufw allow 'Nginx Full'` - разрешает HTTP (80) и HTTPS (443)
- Все остальные порты блокируются

### 9.2 Установка SSL сертификата (рекомендуется)
```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d coworking.greatideas.ru
```

**🔐 Что дает SSL:**
- Шифрование данных между браузером и сервером
- Зеленый замочек в браузере
- Защита от перехвата паролей и личных данных
- Лучший рейтинг в Google (SEO)
- **Let's Encrypt** - выдает бесплатные сертификаты на 90 дней с автообновлением

## Шаг 10: Проверка работы

### 10.1 Проверка сервисов
```bash
systemctl status greatideas
systemctl status nginx
```

### 10.2 Проверка логов
```bash
journalctl -u greatideas -f
tail -f /var/log/nginx/error.log
```

### 10.3 Проверка доступности
- Прямой IP: http://89.110.123.93
- После настройки DNS (до 24 часов): http://coworking.greatideas.ru

## Полезные команды для управления

### Перезапуск после изменений
```bash
systemctl restart greatideas
systemctl restart nginx
```

### Обновление проекта
```bash
cd /var/www/greatideas
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart greatideas
```

### Создание бэкапа
```bash
cd /var/www/greatideas
cp db.sqlite3 db_backup_$(date +%Y%m%d_%H%M%S).sqlite3
```

## Устранение проблем

### Если сайт не открывается:
1. Проверьте статус сервисов: `systemctl status greatideas nginx`
2. Проверьте логи: `journalctl -u greatideas -f`
3. Проверьте конфигурацию Nginx: `nginx -t`
4. Проверьте порты: `netstat -tulpn | grep :80`

### Если ошибки в коде:
1. Проверьте логи Django: `journalctl -u greatideas -f`
2. Перезапустите сервис: `systemctl restart greatideas`
3. Проверьте файл .env и настройки

## 📊 Итоговая архитектура

```
🌍 Интернет (coworking.greatideas.ru)
    ↓ HTTP запрос
🔒 UFW Firewall (порты 22, 80, 443)
    ↓ порт 80
🌐 Nginx (веб-сервер)
    ├── /static/ → 📁 /var/www/greatideas/staticfiles/ (CSS, JS)
    ├── /media/  → 📁 /var/www/greatideas/media/ (изображения)
    └── /        → 🔄 proxy_pass http://127.0.0.1:8000
                      ↓
🔧 Gunicorn (WSGI сервер, 3 worker процесса)
    ↓ WSGI протокол
🐍 Django (ваше приложение)
    ↓ SQL запросы
💾 SQLite база данных
```

**🚀 Производительность:**
- **Nginx** обрабатывает ~50,000 запросов/сек для статики
- **Gunicorn** с 3 worker'ами обрабатывает ~1,000 запросов/сек для Django
- **SQLite** подходит для небольших сайтов (до ~100 одновременных пользователей)

**⚡ Масштабирование (если понадобится):**
- Увеличить количество Gunicorn worker'ов
- Перейти с SQLite на PostgreSQL
- Добавить Redis для кэширования
- Использовать CDN для статических файлов

---

# 🚀 Быстрое развертывание обновлений

## 💡 Концепция разработки

**Локальная разработка → Тестирование → Деплой на сервер**

### Рабочий процесс:
1. **Разрабатываете** на локальном ПК (C:\gibot\greatideas)
2. **Тестируете** локально: `python manage.py runserver`
3. **Готовы к деплою** → запускаете несколько команд
4. **Код автоматически** обновляется на сервере

## 🔧 Настройка Git репозитория (один раз)

### На вашем ПК:
```powershell
cd C:\gibot\greatideas

# Инициализируем Git (если еще не сделано)
git init
git add .
git commit -m "Initial commit"

# Подключаем GitHub/GitLab репозиторий
git remote add origin https://github.com/ваш-username/greatideas.git
git push -u origin main
```

### На сервере (один раз):
```bash
cd /var/www
rm -rf greatideas  # Удаляем старую версию
git clone https://github.com/ваш-username/greatideas.git
cd greatideas

# Настраиваем окружение (как мы делали раньше)
python3 -m venv venv
source venv/bin/activate
pip install django pillow python-decouple gunicorn djangorestframework
```

## 📝 Создание скрипта деплоя

### На сервере создайте файл deploy.sh:
```bash
nano /var/www/deploy.sh
```

Содержимое:
```bash
#!/bin/bash
# Скрипт автоматического деплоя

echo "🚀 Начинаем деплой..."

# Переходим в папку проекта
cd /var/www/greatideas

# Активируем виртуальное окружение
source venv/bin/activate

echo "📥 Загружаем новый код..."
# Получаем последние изменения из Git
git pull origin main

echo "📦 Обновляем зависимости..."
# Обновляем пакеты (если изменился requirements.txt)
pip install -r requirements.txt 2>/dev/null || echo "requirements.txt не найден"

echo "🗄️ Применяем миграции..."
# Применяем изменения БД
python manage.py migrate

echo "📁 Собираем статические файлы..."
# Собираем статику
python manage.py collectstatic --noinput

echo "🔄 Перезапускаем сервер..."
# Перезапускаем Django
systemctl restart greatideas

echo "✅ Деплой завершен!"
echo "🌐 Сайт обновлен: http://coworking.greatideas.ru"

# Проверяем статус
systemctl status greatideas --no-pager -l
```

### Делаем скрипт исполняемым:
```bash
chmod +x /var/www/deploy.sh
```

## ⚡ Процесс быстрого деплоя

### 1. Разработка на локальном ПК:
```powershell
# Работаете с кодом в C:\gibot\greatideas
# Тестируете изменения
python manage.py runserver

# Когда готовы - коммитите изменения
git add .
git commit -m "Добавил новую фичу"
git push origin main
```

### 2. Деплой на сервер (одна команда!):
```bash
ssh root@89.110.123.93 "/var/www/deploy.sh"
```

**Или еще проще** - создайте на своем ПК файл `deploy.bat`:
```batch
@echo off
echo Деплой на сервер...
ssh root@89.110.123.93 "/var/www/deploy.sh"
pause
```

Теперь для деплоя просто запускаете `deploy.bat`!

## 🛠️ Продвинутые улучшения

### 1. Создание requirements.txt (на локальном ПК):
```powershell
# В активированном venv
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Добавил requirements.txt"
git push
```

### 2. Настройка разных .env для локалки и сервера:

**Локальный .env (для разработки):**
```
DEBUG=True
SECRET_KEY=dev-key
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Серверный .env (для продакшена):**
```
DEBUG=False
SECRET_KEY=super-secret-production-key
ALLOWED_HOSTS=localhost,127.0.0.1,89.110.123.93,coworking.greatideas.ru
```

### 3. Горячий деплой без простоя:
```bash
# В deploy.sh замените systemctl restart на:
systemctl reload greatideas  # Graceful restart без простоя
```

### 4. Бэкап перед деплоем:
```bash
# Добавьте в начало deploy.sh:
echo "💾 Создаем бэкап БД..."
cp /var/www/greatideas/db.sqlite3 /var/www/backups/db_$(date +%Y%m%d_%H%M%S).sqlite3
```

## 🔄 Полный workflow разработки

```
🏠 ЛОКАЛЬНАЯ РАЗРАБОТКА
├── Пишете код в VS Code
├── Тестируете: python manage.py runserver
├── git add . && git commit -m "Новая фича"
└── git push origin main

⬇️ ДЕПЛОЙ (1 команда)

🖥️ СЕРВЕР
├── git pull (новый код)
├── pip install (новые пакеты)
├── migrate (обновление БД)  
├── collectstatic (новая статика)
└── restart (перезапуск)

🌐 ГОТОВО!
```

## ⚠️ Важные моменты

1. **Всегда тестируйте локально** перед деплоем
2. **Делайте бэкапы** базы данных перед серьезными изменениями
3. **Используйте ветки Git** для экспериментальных фич
4. **Проверяйте логи** после деплоя: `journalctl -u greatideas -f`

Теперь у вас есть профессиональный workflow! 🎉