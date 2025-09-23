#!/usr/bin/env python
import os
import asyncio
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greatideas.settings')
django.setup()

from telegram_bot.management.commands.run_bot import TelegramBot

async def main():
    """Основная функция для запуска бота"""
    try:
        print("🤖 Запуск Telegram Bot...")
        bot = TelegramBot()
        await bot.run_polling()
    except KeyboardInterrupt:
        print("✅ Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())