"""
Бот для персонала - обработка уведомлений о заказах
"""
import logging
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
from django.core.management.base import BaseCommand
from django.conf import settings
from orders.staff_notifications import staff_notification_service

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class StaffBot:
    """Бот для персонала кафе"""
    
    def __init__(self):
        self.token = settings.STAFF_BOT_TOKEN
        if not self.token:
            raise ValueError("STAFF_BOT_TOKEN не установлен в настройках")
        
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        # Обработчик для кнопки "Доставлено"
        self.application.add_handler(
            CallbackQueryHandler(self.handle_delivery_callback, pattern=r"^deliver_order_\d+$")
        )
    
    async def handle_delivery_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатия кнопки 'Доставлено'"""
        query = update.callback_query
        user = query.from_user
        
        try:
            # Извлекаем ID заказа из callback_data
            callback_data = query.data
            order_id = int(callback_data.split('_')[-1])
            
            # Получаем имя пользователя
            user_name = f"{user.first_name}"
            if user.last_name:
                user_name += f" {user.last_name}"
            if user.username:
                user_name += f" (@{user.username})"
            
            # Отмечаем заказ как доставленный
            success = await staff_notification_service.mark_order_delivered(order_id, user_name)
            
            if success:
                await query.answer("✅ Заказ отмечен как доставленный!", show_alert=True)
                logger.info(f"Заказ {order_id} отмечен как доставленный пользователем {user_name}")
            else:
                await query.answer("❌ Ошибка при обновлении статуса заказа", show_alert=True)
                logger.error(f"Не удалось отметить заказ {order_id} как доставленный")
            
        except ValueError:
            await query.answer("❌ Неверный формат данных", show_alert=True)
            logger.error(f"Неверный callback_data: {query.data}")
        except Exception as e:
            await query.answer("❌ Произошла ошибка", show_alert=True)
            logger.error(f"Ошибка при обработке callback: {e}")
    
    def run_polling(self):
        """Запуск бота в режиме polling"""
        logger.info("Запуск Staff Bot в режиме polling...")
        self.application.run_polling(drop_pending_updates=True)


class Command(BaseCommand):
    """Django management команда для запуска бота персонала"""
    help = 'Запуск Staff Bot для уведомлений персонала'
    
    def handle(self, *args, **options):
        try:
            self.stdout.write("Запуск Staff Bot...")
            bot = StaffBot()
            bot.run_polling()
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.SUCCESS('Staff Bot остановлен')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка: {e}')
            )