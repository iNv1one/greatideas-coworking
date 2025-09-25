import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from django.core.management.base import BaseCommand
from django.conf import settings
from asgiref.sync import sync_to_async

from users.models import TelegramUser

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен в настройках")
        
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        from telegram.ext import PreCheckoutQueryHandler, MessageHandler, filters
        
        self.application.add_handler(CommandHandler("start", self.start_command))
        
        # Обработчики платежей (оставляем для работы веб-приложения)
        self.application.add_handler(PreCheckoutQueryHandler(self.handle_pre_checkout_query))
        self.application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, self.handle_successful_payment))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        
        # Сохраняем или обновляем пользователя в базе данных (через sync_to_async)
        @sync_to_async
        def save_telegram_user():
            telegram_user, created = TelegramUser.objects.get_or_create(
                telegram_id=user.id,
                defaults={
                    'username': user.username or '',
                    'first_name': user.first_name or '',
                    'last_name': user.last_name or '',
                    'language_code': user.language_code or 'ru'
                }
            )
            
            if not created:
                # Обновляем данные существующего пользователя
                telegram_user.username = user.username or ''
                telegram_user.first_name = user.first_name or ''
                telegram_user.last_name = user.last_name or ''
                telegram_user.save()
            
            return telegram_user, created
        
        telegram_user, created = await save_telegram_user()
        
        welcome_text = f"""
🎉 *Добро пожаловать в GreatIdeas Coworking!*

Привет, {user.first_name}! 👋

*GreatIdeas* — это коворкинг с отличной атмосферой.

Нажмите на кнопку ниже, чтобы открыть приложение!
        """
        
        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown'
        )
    

    
    async def handle_pre_checkout_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик pre-checkout запросов (подтверждение платежа)"""
        query = update.pre_checkout_query
        
        try:
            # Подтверждаем платеж
            await query.answer(ok=True)
            logger.info(f"Pre-checkout подтвержден для пользователя {query.from_user.id}")
        except Exception as e:
            logger.error(f"Ошибка при обработке pre-checkout: {e}")
            await query.answer(ok=False, error_message="Произошла ошибка при обработке платежа")
    
    async def handle_successful_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик успешных платежей"""
        payment = update.message.successful_payment
        user = update.effective_user
        
        try:
            logger.info(f"Успешный платеж от пользователя {user.id}: {payment.total_amount/100} {payment.currency}")
            logger.info(f"Invoice payload: {payment.invoice_payload}")
            logger.info(f"Provider payment charge id: {payment.provider_payment_charge_id}")
            
            # Найти заказ по invoice_payload или provider_payment_charge_id
            order = await self._find_order_by_payment(payment)
            
            if order:
                # Обновить статус заказа
                await self._update_order_status(order, 'confirmed')
                
                # Отправить уведомление персоналу
                await self._notify_staff_about_order(order)
                
                # Очистить корзину пользователя
                await self._clear_user_cart(user.id)
                
                # Отправляем подтверждение пользователю с номером заказа и ссылкой для отслеживания
                tracking_url = f"https://coworking.greatideas.ru/orders/status/{order.order_number}/"
                
                keyboard = [
                    [InlineKeyboardButton("🔍 Отследить заказ", url=tracking_url)]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"✅ *Платеж успешен!*\n"
                    f"Номер заказа: *#{order.order_number}*\n"
                    f"Сумма: {payment.total_amount/100} {payment.currency}\n"
                    f"Спасибо за покупку! 🎉\n\n"
                    f"📋 Ваш заказ передан в кафе и готовится.\n"
                    f"🔔 Вы получите уведомление, когда заказ будет готов.\n\n"
                    f"🏪 Кафе: {order.cafe.name}\n"
                    f"📍 {order.cafe.address}\n\n"
                    f"👆 *Нажмите кнопку выше для отслеживания заказа*",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            else:
                # Если заказ не найден
                await update.message.reply_text(
                    f"✅ *Платеж успешен!*\n"
                    f"Сумма: {payment.total_amount/100} {payment.currency}\n"
                    f"Спасибо за покупку! 🎉\n\n"
                    f"Ваш заказ передан в обработку.",
                    parse_mode='Markdown'
                )
            
        except Exception as e:
            logger.error(f"Ошибка при обработке успешного платежа: {e}")
    
    @sync_to_async
    def _find_order_by_payment(self, payment):
        """Найти заказ по данным платежа"""
        from payments.models import Payment as PaymentModel
        
        try:
            # Сначала ищем по invoice_payload
            if payment.invoice_payload:
                payment_record = PaymentModel.objects.filter(
                    invoice_payload=payment.invoice_payload
                ).first()
                if payment_record:
                    return payment_record.order
            
            # Затем по provider_payment_charge_id
            if payment.provider_payment_charge_id:
                payment_record = PaymentModel.objects.filter(
                    provider_payment_charge_id=payment.provider_payment_charge_id
                ).first()
                if payment_record:
                    return payment_record.order
            
            return None
        except Exception as e:
            logger.error(f"Ошибка поиска заказа: {e}")
            return None
    
    @sync_to_async
    def _update_order_status(self, order, status):
        """Обновить статус заказа"""
        try:
            order.status = status
            order.save(update_fields=['status'])
            logger.info(f"Статус заказа #{order.order_number} обновлен на '{status}'")
        except Exception as e:
            logger.error(f"Ошибка обновления статуса заказа: {e}")
    
    async def _notify_staff_about_order(self, order):
        """Отправить уведомление персоналу о новому заказе"""
        try:
            from orders.staff_notifications import staff_notification_service
            # Используем синхронную версию напрямую в sync_to_async
            await sync_to_async(staff_notification_service.send_new_order_notification_sync)(order)
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления персоналу: {e}")
    

    
    @sync_to_async
    def _clear_user_cart(self, telegram_user_id):
        """Очистить корзину пользователя"""
        try:
            from users.models import TelegramUser
            from orders.models import Order
            telegram_user = TelegramUser.objects.filter(telegram_id=telegram_user_id).first()
            if telegram_user:
                # Удаляем все заказы пользователя со статусом 'pending' (корзина)
                pending_orders = Order.objects.filter(user=telegram_user, status='pending')
                count = pending_orders.count()
                for order in pending_orders:
                    order.delete()
                logger.info(f"Удалено {count} заказов-корзин пользователя {telegram_user_id}")
        except Exception as e:
            logger.error(f"Ошибка очистки корзины: {e}")
    
    def run_polling(self):
        """Запуск бота в режиме polling"""
        logger.info("Запуск Telegram Bot в режиме polling...")
        # Используем синхронный метод run_polling, который сам управляет event loop
        self.application.run_polling(drop_pending_updates=True)


class Command(BaseCommand):
    help = 'Запуск Telegram Bot'
    
    def handle(self, *args, **options):
        try:
            self.stdout.write("Запуск Telegram Bot...")
            bot = TelegramBot()
            
            # Запуск через синхронный метод
            bot.run_polling()
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.SUCCESS('Бот остановлен')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка: {e}')
            )