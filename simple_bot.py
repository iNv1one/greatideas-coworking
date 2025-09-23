#!/usr/bin/env python
"""
Простой запуск Telegram бота без конфликтов event loop
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greatideas.settings')
django.setup()

# Импорт после настройки Django
from telegram_bot.management.commands.run_bot import TelegramBot

def main():
    """Простой запуск бота"""
    try:
        print("🤖 Запуск Telegram Bot...")
        
        # Создаем бота
        bot = TelegramBot()
        
        # Запускаем бота напрямую через python-telegram-bot
        bot.application.run_polling(drop_pending_updates=True)
        
    except KeyboardInterrupt:
        print("✅ Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()