import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from django.core.management.base import BaseCommand
from django.conf import settings
from asgiref.sync import sync_to_async
from cafes.models import Cafe
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
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("orders", self.orders_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Обработчики платежей
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
🎉 *Добро пожаловать в GreatIdeas!*

Привет, {user.first_name}! 👋

*GreatIdeas* — это сеть уютных кафе с отличной едой и атмосферой. Мы объединили лучшие заведения города под одной крышей!

🏪 *Что мы предлагаем:*
• Несколько уникальных кафе
• Разнообразное меню в каждом заведении  
• Удобный заказ через бот
• Быстрая доставка или самовывоз

Выберите действие:
        """
        
        # Создаем клавиатуру с кнопками
        keyboard = [
            [InlineKeyboardButton("🏪 Выбрать кафе", callback_data="show_cafes")],
            [InlineKeyboardButton("📋 Мои заказы", callback_data="my_orders")],
            [InlineKeyboardButton("ℹ️ О сервисе", callback_data="about_service")],
            [InlineKeyboardButton("🌐 Открыть веб-сайт", url="https://coworking.greatideas.ru/")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
🤖 *Справка по боту GreatIdeas*

*Доступные команды:*
/start - Главное меню
/help - Эта справка
/orders - Мои заказы

*Как сделать заказ:*
1️⃣ Нажмите "Выбрать кафе"
2️⃣ Выберите понравившееся кафе
3️⃣ Перейдите на страницу кафе
4️⃣ Добавьте блюда в корзину
5️⃣ Оформите заказ

*Способы получения:*
🚶‍♂️ Самовывоз - бесплатно
🏍️ Доставка - по тарифам кафе

*Нужна помощь?*
Напишите нам или используйте команду /start
        """
        
        keyboard = [
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
            [InlineKeyboardButton("🏪 Выбрать кафе", callback_data="show_cafes")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def orders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /orders"""
        await self.show_user_orders(update, context, is_message=True)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на inline кнопки"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "main_menu":
            await self.show_main_menu(query)
        elif query.data == "show_cafes":
            await self.show_cafes(query)
        elif query.data == "my_orders":
            await self.show_user_orders(query, context=None, is_message=False)
        elif query.data == "about_service":
            await self.show_about_service(query)
        elif query.data.startswith("cafe_"):
            cafe_id = query.data.replace("cafe_", "")
            await self.show_cafe_details(query, cafe_id)
    
    async def show_main_menu(self, query):
        """Показать главное меню"""
        user = query.from_user
        
        welcome_text = f"""
🎉 *GreatIdeas - Главное меню*

Привет, {user.first_name}! 👋

Выберите действие:
        """
        
        keyboard = [
            [InlineKeyboardButton("🏪 Выбрать кафе", callback_data="show_cafes")],
            [InlineKeyboardButton("ℹ️ О сервисе", callback_data="about_service")],
            [InlineKeyboardButton("🌐 Открыть веб-сайт", url="https://coworking.greatideas.ru/")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def show_cafes(self, query):
        """Показать список кафе"""
        @sync_to_async
        def get_cafes():
            return list(Cafe.objects.filter(is_active=True).order_by('name'))
        
        cafes = await get_cafes()
        
        if not cafes:
            text = """
😔 *Кафе временно недоступны*

К сожалению, в данный момент все кафе закрыты или проходят обновление.

Попробуйте зайти позже!
            """
            keyboard = [
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
            ]
        else:
            text = f"""
🏪 *Выберите кафе ({len(cafes)} доступно)*

Каждое кафе имеет уникальное меню и атмосферу:
            """
            
            keyboard = []
            for cafe in cafes:
                keyboard.append([
                    InlineKeyboardButton(
                        f"☕ {cafe.name}",
                        callback_data=f"cafe_{cafe.id}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def show_cafe_details(self, query, cafe_id):
        """Показать детали кафе"""
        @sync_to_async
        def get_cafe():
            try:
                return Cafe.objects.get(id=cafe_id, is_active=True)
            except Cafe.DoesNotExist:
                return None
        
        cafe = await get_cafe()
        
        if cafe:
            
            text = f"""
☕ *{cafe.name}*

{cafe.description}

📍 *Адрес:* {cafe.address}
🕒 *Время работы:* {cafe.working_hours}
📞 *Телефон:* {cafe.phone}
"""
            
            if cafe.min_order_amount > 0:
                text += f"💰 *Минимальный заказ:* {cafe.min_order_amount} ₽\n"
            
            if cafe.delivery_fee > 0:
                text += f"🚚 *Доставка:* {cafe.delivery_fee} ₽\n"
            
            text += f"""

🍽️ Откройте меню кафе и добавляйте блюда в корзину!
            """
            
            keyboard = [
                [InlineKeyboardButton(
                    "🍽️ Открыть меню", 
                    url=f"https://coworking.greatideas.ru/cafe/{cafe.id}/"
                )],
                [InlineKeyboardButton("🏪 Другие кафе", callback_data="show_cafes")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
        else:
            text = "😔 Кафе не найдено или временно недоступно"
            keyboard = [
                [InlineKeyboardButton("🏪 Выбрать другое", callback_data="show_cafes")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def show_about_service(self, query):
        """Показать информацию о сервисе"""
        text = """
ℹ️ *О сервисе GreatIdeas*

*GreatIdeas* — это современная сеть кафе, которая объединяет лучшие заведения города под единой платформой.

🎯 *Наша миссия:*
Сделать заказ еды максимально удобным и быстрым, сохраняя уникальность каждого кафе.

✨ *Преимущества:*
• 🏪 Несколько уникальных кафе
• 🍽️ Разнообразное меню
• 📱 Удобный заказ через Telegram
• ⚡ Быстрое приготовление
• 🚚 Доставка или самовывоз
• 💳 Удобная оплата

🏆 *Качество:*
• Только свежие продукты
• Проверенные поставщики  
• Контроль качества
• Обратная связь

*Присоединяйтесь к нашему сообществу любителей вкусной еды!*
        """
        
        keyboard = [
            [InlineKeyboardButton("🏪 Выбрать кафе", callback_data="show_cafes")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    async def show_user_orders(self, update_or_query, context, is_message=False):
        """Показать заказы пользователя"""
        user = update_or_query.effective_user if is_message else update_or_query.from_user
        
        try:
            # Получаем заказы пользователя
            orders = await self._get_user_orders(user.id)
            
            if not orders:
                text = """
📋 *Мои заказы*

У вас пока нет заказов.
Выберите кафе и сделайте свой первый заказ! 🎉
                """
                
                keyboard = [
                    [InlineKeyboardButton("🏪 Выбрать кафе", callback_data="show_cafes")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
                ]
            else:
                text = "📋 *Мои заказы*\n\n"
                
                # Показываем последние 5 заказов
                for i, order in enumerate(orders[:5], 1):
                    status_emoji = {
                        'pending': '⏳',
                        'confirmed': '✅',
                        'preparing': '👨‍🍳',
                        'ready': '🎯',
                        'delivered': '✅',
                        'cancelled': '❌'
                    }.get(order['status'], '❓')
                    
                    text += f"{i}. *Заказ #{order['order_number']}*\n"
                    text += f"   {status_emoji} {order['status_display']}\n"
                    text += f"   🏪 {order['cafe_name']}\n"
                    text += f"   💰 {order['total_amount']} ₽\n"
                    text += f"   📅 {order['created_at']}\n\n"
                
                if len(orders) > 5:
                    text += f"... и еще {len(orders) - 5} заказов\n\n"
                
                # Добавляем ссылку на полный список
                orders_url = "https://coworking.greatideas.ru/orders/my-orders/"
                text += f"👆 *[Посмотреть все заказы на сайте]({orders_url})*"
                
                keyboard = [
                    [InlineKeyboardButton("🌐 Все заказы на сайте", url=orders_url)],
                    [InlineKeyboardButton("🏪 Сделать новый заказ", callback_data="show_cafes")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
                ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if is_message:
                await update_or_query.reply_text(
                    text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            else:
                await update_or_query.edit_message_text(
                    text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                
        except Exception as e:
            logger.error(f"Ошибка при получении заказов пользователя: {e}")
            error_text = "❌ Произошла ошибка при загрузке ваших заказов. Попробуйте позже."
            
            keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if is_message:
                await update_or_query.reply_text(error_text, reply_markup=reply_markup)
            else:
                await update_or_query.edit_message_text(error_text, reply_markup=reply_markup)
    
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
    def _get_user_orders(self, telegram_user_id):
        """Получить заказы пользователя"""
        try:
            from users.models import TelegramUser
            from orders.models import Order
            from django.utils import timezone
            
            telegram_user = TelegramUser.objects.filter(telegram_id=telegram_user_id).first()
            if not telegram_user:
                return []
            
            orders = Order.objects.filter(user=telegram_user).order_by('-created_at')
            
            orders_data = []
            for order in orders:
                orders_data.append({
                    'order_number': order.order_number,
                    'status': order.status,
                    'status_display': order.get_status_display(),
                    'cafe_name': order.cafe.name,
                    'total_amount': float(order.total_amount),
                    'created_at': order.created_at.strftime('%d.%m.%Y %H:%M'),
                    'delivered_at': order.delivered_at.strftime('%d.%m.%Y %H:%M') if order.delivered_at else None,
                })
            
            return orders_data
            
        except Exception as e:
            logger.error(f"Ошибка получения заказов пользователя: {e}")
            return []
    
    @sync_to_async
    def _clear_user_cart(self, telegram_user_id):
        """Очистить корзину пользователя"""
        try:
            from users.models import TelegramUser
            
            telegram_user = TelegramUser.objects.filter(telegram_id=telegram_user_id).first()
            if telegram_user:
                # Здесь можно добавить логику очистки корзины
                # Например, если корзина хранится в сессии пользователя или в отдельной модели
                logger.info(f"Корзина пользователя {telegram_user_id} очищена")
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