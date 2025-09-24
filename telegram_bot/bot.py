import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, LabeledPrice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, PreCheckoutQueryHandler, MessageHandler, filters
from django.core.management.base import BaseCommand
from django.conf import settings
from cafes.models import Cafe
from users.models import TelegramUser
from orders.telegram_payments import TelegramPaymentService

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
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("pay", self.test_payment_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(PreCheckoutQueryHandler(self.pre_checkout_callback))
        self.application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, self.successful_payment_callback))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        
        # Сохраняем или обновляем пользователя в базе данных
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
        
        welcome_text = f"""
🎉 *Добро пожаловать в GreatIdeas!*

Привет, {user.first_name}! 👋

*GreatIdeas* — это сеть уютных кафе с отличной едой и атмосферой. 

🏪 *Что мы предлагаем:*
• Несколько уникальных кафе
• Разнообразное меню в каждом заведении  
• Удобный заказ через приложение
• Быстрая доставка или самовывоз

Откройте наше приложение для заказа:
        """
        
        # Создаем клавиатуру с Web App кнопкой
        web_app_url = "http://127.0.0.1:8000/"  # Замените на ваш домен
        keyboard = [
            [InlineKeyboardButton(
                "� Открыть GreatIdeas", 
                web_app=WebAppInfo(url=web_app_url)
            )],
            [InlineKeyboardButton("ℹ️ О сервисе", callback_data="about_service")],
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
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на inline кнопки"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "main_menu":
            await self.show_main_menu(query)
        elif query.data == "show_cafes":
            await self.show_cafes(query)
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
            [InlineKeyboardButton("🌐 Открыть веб-сайт", url="http://127.0.0.1:8000/")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def show_cafes(self, query):
        """Показать список кафе"""
        cafes = Cafe.objects.filter(is_active=True).order_by('name')
        
        if not cafes.exists():
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
🏪 *Выберите кафе ({cafes.count()} доступно)*

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
        try:
            cafe = Cafe.objects.get(id=cafe_id, is_active=True)
            
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
                    url=f"http://127.0.0.1:8000/cafe/{cafe.id}/"
                )],
                [InlineKeyboardButton("🏪 Другие кафе", callback_data="show_cafes")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
        except Cafe.DoesNotExist:
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
    
    async def test_payment_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для тестирования платежей"""
        user = update.effective_user
        
        # Создаем тестовый инвойс
        title = "Тестовый заказ GreatIdeas"
        description = "Тестирование платежной системы с ЮKassa"
        payload = f"test_payment_{user.id}"
        currency = "RUB"
        
        # Тестовые цены (в копейках)
        prices = [
            LabeledPrice("Кофе Латте", 25000),  # 250 рублей
            LabeledPrice("Круассан", 15000),    # 150 рублей
        ]
        
        await context.bot.send_invoice(
            chat_id=update.effective_chat.id,
            title=title,
            description=description,
            payload=payload,
            provider_token=settings.PAYMENT_PROVIDER_TOKEN,
            currency=currency,
            prices=prices,
            photo_url="https://via.placeholder.com/300x200?text=GreatIdeas+Test",
            need_name=True,
            need_phone_number=True,
            need_email=False,
            need_shipping_address=False,
            is_flexible=False,
        )
    
    async def create_order_invoice(self, chat_id: int, telegram_user_id: int, cart_data: dict, context: ContextTypes.DEFAULT_TYPE):
        """Создает инвойс для заказа из корзины"""
        try:
            payment_service = TelegramPaymentService()
            telegram_user = TelegramUser.objects.get(telegram_id=telegram_user_id)
            
            # Создаем заказ из корзины
            order = payment_service.create_order_from_cart(
                telegram_user=telegram_user,
                cart_data=cart_data,
                delivery_type='pickup',  # По умолчанию самовывоз
            )
            
            # Создаем платеж
            payment = payment_service.create_payment(order)
            
            # Создаем список цен для инвойса
            prices = payment_service.create_invoice_prices(order)
            
            title = f"Заказ #{order.order_number}"
            description = f"Заказ в {order.cafe.name}\nВсего позиций: {order.items.count()}"
            
            await context.bot.send_invoice(
                chat_id=chat_id,
                title=title,
                description=description,
                payload=payment.invoice_payload,
                provider_token=settings.PAYMENT_PROVIDER_TOKEN,
                currency=payment.currency,
                prices=prices,
                photo_url=order.cafe.logo.url if order.cafe.logo else None,
                need_name=True,
                need_phone_number=True,
                need_email=False,
                need_shipping_address=order.delivery_type == 'delivery',
                is_flexible=False,
            )
            
            return order
            
        except Exception as e:
            logger.error(f"Ошибка создания инвойса: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Произошла ошибка при создании инвойса. Попробуйте позже."
            )
            return None
    
    async def pre_checkout_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик pre_checkout_query"""
        query = update.pre_checkout_query
        
        try:
            # Проверяем заказ
            payment_service = TelegramPaymentService()
            order = payment_service.get_order_by_payment_payload(query.invoice_payload)
            
            # Проверяем, что заказ еще не оплачен
            if order.status == 'paid':
                await query.answer(
                    ok=False, 
                    error_message="Этот заказ уже оплачен"
                )
                return
            
            # Все проверки пройдены
            await query.answer(ok=True)
            
        except Exception as e:
            logger.error(f"Ошибка в pre_checkout: {e}")
            await query.answer(
                ok=False, 
                error_message="Произошла ошибка при проверке заказа"
            )
    
    async def successful_payment_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик успешного платежа"""
        payment_info = update.message.successful_payment
        
        try:
            payment_service = TelegramPaymentService()
            
            # Обрабатываем платеж
            order = payment_service.process_successful_payment({
                'invoice_payload': payment_info.invoice_payload,
                'telegram_payment_charge_id': payment_info.telegram_payment_charge_id,
                'provider_payment_charge_id': payment_info.provider_payment_charge_id,
            })
            
            # Отправляем подтверждение
            success_text = f"""
✅ *Платеж успешно обработан!*

*Заказ:* #{order.order_number}
*Кафе:* {order.cafe.name}
*Сумма:* {order.total_amount} ₽
*Статус:* Оплачен

Ваш заказ принят в работу. Мы уведомим вас о готовности!

*Детали заказа:*
"""
            
            for item in order.items.all():
                success_text += f"• {item.menu_item.name}"
                if item.variant:
                    success_text += f" ({item.variant.name})"
                success_text += f" x{item.quantity} - {item.total_price} ₽\n"
            
            await update.message.reply_text(
                success_text,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка обработки платежа: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке платежа. Обратитесь в поддержку."
            )
    
    async def run_polling(self):
        """Запуск бота в режиме polling"""
        logger.info("Запуск Telegram Bot в режиме polling...")
        await self.application.run_polling(drop_pending_updates=True)


class Command(BaseCommand):
    help = 'Запуск Telegram Bot'
    
    def handle(self, *args, **options):
        try:
            bot = TelegramBot()
            asyncio.run(bot.run_polling())
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.SUCCESS('Бот остановлен')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка: {e}')
            )