#!/usr/bin/env python
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greatideas.settings')
django.setup()

from django.core.management import execute_from_command_line

if __name__ == "__main__":
    try:
        print("🤖 Запуск Telegram Bot...")
        execute_from_command_line(['manage.py', 'run_bot'])
    except KeyboardInterrupt:
        print("✅ Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")