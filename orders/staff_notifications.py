"""
Сервис для отправки уведомлений персоналу о новых заказах
"""
import logging
import asyncio
from typing import Optional
from django.conf import settings
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class StaffNotificationService:
    """Сервис для управления уведомлениями персонала"""
    
    def __init__(self):
        self.bot_token = settings.STAFF_BOT_TOKEN
        self.chat_id = settings.STAFF_CHAT_ID
        
        if not self.bot_token:
            raise ValueError("STAFF_BOT_TOKEN не установлен в настройках")
        
        if not self.chat_id:
            logger.warning("STAFF_CHAT_ID не установлен. Уведомления не будут отправляться.")
        
        self.bot = Bot(token=self.bot_token)
    
    def send_new_order_notification_sync(self, order) -> Optional[int]:
        """Синхронная отправка уведомления о новом заказе"""
        try:
            import requests
            from django.utils import timezone
            
            if not self.chat_id:
                logger.warning("STAFF_CHAT_ID не установлен. Уведомление не отправлено.")
                return None
            
            # Формируем текст уведомления синхронно
            message_text = self._format_order_message_sync(order)
            
            # Создаем клавиатуру с кнопкой "Доставлено"
            keyboard = {
                "inline_keyboard": [[{
                    "text": "✅ Доставлено",
                    "callback_data": f"deliver_order_{order.id}"
                }]]
            }
            
            # Отправляем сообщение через HTTP API
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message_text,
                'parse_mode': 'Markdown',
                'reply_markup': keyboard
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    message_id = result['result']['message_id']
                    
                    # Обновляем заказ
                    order.staff_notification_sent = True
                    order.staff_message_id = message_id
                    order.save(update_fields=['staff_notification_sent', 'staff_message_id'])
                    
                    logger.info(f"Уведомление о заказе #{order.order_number} отправлено персоналу")
                    return message_id
                else:
                    logger.error(f"Telegram API ошибка: {result.get('description', 'Unknown error')}")
                    return None
            else:
                logger.error(f"HTTP ошибка при отправке уведомления: {response.status_code}")
                return None
            
        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке уведомления: {e}")
            return None
    
    async def send_new_order_notification(self, order) -> Optional[int]:
        """
        Отправить уведомление о новом заказе персоналу
        
        Args:
            order: объект модели Order
            
        Returns:
            int: ID отправленного сообщения или None при ошибке
        """
        if not self.chat_id:
            logger.warning("STAFF_CHAT_ID не установлен. Уведомление не отправлено.")
            return None
        
        try:
            # Формируем текст уведомления
            message_text = await self._format_order_message(order)
            
            # Создаем клавиатуру с кнопкой "Доставлено"
            keyboard = InlineKeyboardButton(
                "✅ Доставлено", 
                callback_data=f"deliver_order_{order.id}"
            )
            reply_markup = InlineKeyboardMarkup([[keyboard]])
            
            # Отправляем сообщение
            message = await self.bot.send_message(
                chat_id=self.chat_id,
                text=message_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            # Обновляем заказ
            await self._update_order_notification_status(order, message.message_id)
            
            logger.info(f"Уведомление о заказе #{order.order_number} отправлено персоналу")
            return message.message_id
            
        except TelegramError as e:
            logger.error(f"Ошибка отправки уведомления о заказе #{order.order_number}: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке уведомления: {e}")
            return None
    
    async def _format_order_message(self, order) -> str:
        """Форматировать сообщение с информацией о заказе"""
        
        # Получаем позиции заказа
        items_text = ""
        items = await sync_to_async(lambda: list(order.items.all()))()
        
        for order_item in items:
            item_text = f"• {order_item.menu_item.name}"
            
            if order_item.variant:
                item_text += f" ({order_item.variant.name})"
            
            if order_item.quantity > 1:
                item_text += f" x{order_item.quantity}"
            
            # Проверяем есть ли добавки
            if await sync_to_async(order_item.selected_addons.exists)():
                addons = await sync_to_async(lambda: list(order_item.selected_addons.all()))()
                addon_names = [addon.addon.name for addon in addons]
                item_text += f" + {', '.join(addon_names)}"
            
            item_text += f" - {order_item.total_price} ₽"
            items_text += item_text + "\n"
        
        # Определяем тип получения
        delivery_type = "🏃 Самовывоз" if order.delivery_type == 'pickup' else "🚚 Доставка"
        
        message_text = f"""
🆕 *НОВЫЙ ЗАКАЗ #{order.order_number}*

🏪 *Кафе:* {order.cafe.name}
👤 *Клиент:* {order.customer_name}
📞 *Телефон:* {order.customer_phone}
{delivery_type}

📋 *Состав заказа:*
{items_text}
💰 *Общая сумма:* {order.total_amount} ₽

⏰ *Время заказа:* {order.created_at.strftime('%H:%M')}
"""
        
        if order.delivery_type == 'delivery' and order.delivery_address:
            message_text += f"📍 *Адрес доставки:* {order.delivery_address}\n"
        
        if order.comment:
            message_text += f"💬 *Комментарий:* {order.comment}\n"
        
        return message_text.strip()
    
    def _format_order_message_sync(self, order) -> str:
        """Синхронная версия форматирования сообщения с информацией о заказе"""
        
        # Получаем позиции заказа
        items_text = ""
        items = list(order.items.all())
        
        for order_item in items:
            item_text = f"• {order_item.menu_item.name}"
            
            if order_item.variant:
                item_text += f" ({order_item.variant.name})"
            
            if order_item.quantity > 1:
                item_text += f" x{order_item.quantity}"
            
            # Проверяем есть ли добавки
            if order_item.selected_addons.exists():
                addons = list(order_item.selected_addons.all())
                addon_names = [addon.addon.name for addon in addons]
                item_text += f" + {', '.join(addon_names)}"
            
            item_text += f" - {order_item.total_price} ₽"
            items_text += item_text + "\n"
        
        # Определяем тип получения
        delivery_type = "🏃 Самовывоз" if order.delivery_type == 'pickup' else "🚚 Доставка"
        
        message_text = f"""
🆕 *НОВЫЙ ЗАКАЗ #{order.order_number}*

🏪 *Кафе:* {order.cafe.name}
👤 *Клиент:* {order.customer_name}
📞 *Телефон:* {order.customer_phone}
{delivery_type}

📋 *Состав заказа:*
{items_text}
💰 *Общая сумма:* {order.total_amount} ₽

⏰ *Время заказа:* {order.created_at.strftime('%H:%M')}
"""
        
        if order.delivery_type == 'delivery' and order.delivery_address:
            message_text += f"📍 *Адрес доставки:* {order.delivery_address}\n"
        
        if order.comment:
            message_text += f"💬 *Комментарий:* {order.comment}\n"
        
        return message_text.strip()
    
    @sync_to_async
    def _update_order_notification_status(self, order, message_id: int):
        """Обновить статус уведомления заказа"""
        order.staff_notification_sent = True
        order.staff_message_id = message_id
        order.save(update_fields=['staff_notification_sent', 'staff_message_id'])
    
    async def mark_order_delivered(self, order_id: int, user_name: str = "Персонал") -> bool:
        """
        Отметить заказ как доставленный
        
        Args:
            order_id: ID заказа
            user_name: Имя пользователя, который отметил доставку
            
        Returns:
            bool: True если успешно, False при ошибке
        """
        try:
            from django.utils import timezone
            from .models import Order
            
            # Получаем заказ
            order = await sync_to_async(Order.objects.get)(id=order_id)
            
            # Обновляем статус
            order.status = 'delivered'
            order.delivered_at = timezone.now()
            await sync_to_async(order.save)(update_fields=['status', 'delivered_at'])
            
            # Обновляем сообщение в чате персонала
            if order.staff_message_id:
                await self._update_staff_message(order, user_name)
            
            logger.info(f"Заказ #{order.order_number} отмечен как доставленный пользователем {user_name}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отметке заказа {order_id} как доставленного: {e}")
            return False
    
    async def _update_staff_message(self, order, user_name: str):
        """Обновить сообщение в чате персонала после доставки"""
        try:
            new_text = f"✅ *ЗАКАЗ #{order.order_number} ДОСТАВЛЕН*\n\n"
            new_text += f"👤 Доставил: {user_name}\n"
            new_text += f"⏰ Время доставки: {order.delivered_at.strftime('%H:%M')}\n"
            new_text += f"🏪 Кафе: {order.cafe.name}\n"
            new_text += f"👤 Клиент: {order.customer_name}"
            
            await self.bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=order.staff_message_id,
                text=new_text,
                parse_mode='Markdown'
            )
            
        except TelegramError as e:
            logger.error(f"Не удалось обновить сообщение в чате персонала: {e}")


# Глобальный экземпляр сервиса
staff_notification_service = StaffNotificationService()