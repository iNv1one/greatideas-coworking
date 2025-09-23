"""
Простой скрипт для запуска Telegram бота
"""
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# Токен вашего бота
BOT_TOKEN = "8471807616:AAGSX43m5T7N64t-Wm6oOsk6sILH9pnxkZw"
# URL вашего Web App - временно используем Replit или любой HTTPS домен
WEB_APP_URL = "https://example.com"  # Замените на ваш HTTPS домен

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    
    welcome_text = f"""
🎉 Добро пожаловать в GreatIdeas, {user.first_name}!

🍕 Лучшая сеть кафе для работы и отдыха
☕ Заказывайте еду и напитки прямо через Telegram
📱 Удобно, быстро, вкусно!

Нажмите кнопку ниже, чтобы перейти на наш сайт и войти через Telegram:
    """
    
    # Создаем кнопку для открытия Web App (временно отключено)
    keyboard = [
        [InlineKeyboardButton(
            "� Открыть сайт", 
            url="http://localhost:8000/users/telegram-login/"
        )],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = """
🆘 Помощь по использованию GreatIdeas Bot

📋 Доступные команды:
/start - Открыть главное меню
/help - Показать эту справку

🍕 Как заказать:
1. Нажмите "Открыть GreatIdeas"
2. Выберите кафе
3. Добавьте товары в корзину
4. Оформите заказ

📞 Поддержка: напишите сюда в чат
    """
    
    await update.message.reply_text(help_text)

def main():
    """Запуск бота"""
    print(f"🤖 Запуск Telegram бота...")
    print(f"🌐 Web App URL: {WEB_APP_URL}")
    print(f"📱 Username: @gi_coworking_bot")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Запускаем бота
    print("✅ Бот запущен! Нажмите Ctrl+C для остановки.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()