"""
API views для работы с платежами
"""
import json
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from telegram import Bot
from users.models import TelegramUser
from orders.models import Order
from orders.telegram_payments import TelegramPaymentService

logger = logging.getLogger(__name__)


def is_working_hours():
    """Проверка рабочего времени (10:00-18:45 МСК)"""
    # Получаем текущее время в московском часовом поясе
    moscow_tz = timezone(timedelta(hours=3))
    moscow_time = datetime.now(moscow_tz)
    
    hour = moscow_time.hour
    minute = moscow_time.minute
    
    # Рабочее время: 10:00-18:45
    if hour < 10:
        return False
    if hour > 18:
        return False
    if hour == 18 and minute > 45:
        return False
    
    return True


def send_invoice_sync(telegram_id, title, description, payload, prices, photo_url=None, need_shipping=False):
    """Синхронная обертка для отправки инвойса"""
    async def _send_invoice():
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        await bot.send_invoice(
            chat_id=telegram_id,
            title=title,
            description=description,
            payload=payload,
            provider_token=settings.PAYMENT_PROVIDER_TOKEN,
            currency='RUB',
            prices=prices,
            photo_url=photo_url,
            need_name=True,
            need_phone_number=True,
            need_email=False,
            need_shipping_address=need_shipping,
            is_flexible=False,
        )
    
    # Выполняем асинхронную функцию синхронно
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_send_invoice())


@csrf_exempt
@require_http_methods(["POST"])
def create_payment(request):
    """
    API endpoint для создания платежа из веб-интерфейса
    
    Ожидаемые данные:
    {
        "telegram_id": 123456789,
        "cart_data": {...},
        "delivery_type": "pickup",
        "customer_name": "Имя",
        "customer_phone": "+7...",
        "delivery_address": "",
        "comment": ""
    }
    """
    try:
        # Проверяем рабочее время
        if not is_working_hours():
            moscow_tz = timezone(timedelta(hours=3))
            current_time = datetime.now(moscow_tz).strftime('%H:%M')
            return JsonResponse({
                'success': False,
                'error': f'К сожалению, заказы принимаются только с 10:00 до 18:45 (МСК). Сейчас: {current_time}. Пожалуйста, попробуйте оформить заказ в рабочее время.'
            }, status=400)

        data = json.loads(request.body)
        
        # Проверяем обязательные поля
        telegram_id = data.get('telegram_id')
        cart_data = data.get('cart_data', {})
        
        if not telegram_id:
            return JsonResponse({
                'success': False,
                'error': 'telegram_id обязателен'
            }, status=400)
        
        if not cart_data:
            return JsonResponse({
                'success': False,
                'error': 'Корзина пуста'
            }, status=400)
        
        # Получаем пользователя Telegram
        try:
            telegram_user = TelegramUser.objects.get(telegram_id=telegram_id)
        except TelegramUser.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Пользователь не найден'
            }, status=404)
        
        # Проверяем, есть ли активные заказы у пользователя (за последние 5 минут)
        from django.utils import timezone
        from datetime import timedelta
        
        recent_orders = Order.objects.filter(
            user=telegram_user,
            status__in=['pending', 'confirmed'],
            created_at__gte=timezone.now() - timedelta(minutes=5)
        ).exists()
        
        if recent_orders:
            return JsonResponse({
                'success': False,
                'error': 'У вас уже есть активный заказ. Подождите несколько минут перед созданием нового.'
            }, status=400)
        
        # Создаем сервис платежей
        payment_service = TelegramPaymentService()
        
        # Проверяем обязательное поле workspace_number
        workspace_number = data.get('workspace_number')
        if not workspace_number or workspace_number < 1 or workspace_number > 30:
            return JsonResponse({
                'success': False,
                'error': 'Необходимо выбрать номер рабочего места (от 1 до 30)'
            }, status=400)
        
        # Создаем заказ
        order = payment_service.create_order_from_cart(
            telegram_user=telegram_user,
            cart_data=cart_data,
            delivery_type=data.get('delivery_type', 'pickup'),
            customer_name=data.get('customer_name', ''),
            customer_phone=data.get('customer_phone', ''),
            delivery_address=data.get('delivery_address', ''),
            workspace_number=workspace_number,
            comment=data.get('comment', ''),
        )
        
        # Создаем платеж
        payment = payment_service.create_payment(order)
        
        # Создаем список цен для инвойса
        prices = payment_service.create_invoice_prices(order)
        
        title = f"Заказ #{order.order_number}"
        description = f"Заказ в {order.cafe.name}\nВсего позиций: {order.items.count()}"
        
        # Отправляем инвойс пользователю
        send_invoice_sync(
            telegram_id=telegram_id,
            title=title,
            description=description,
            payload=payment.invoice_payload,
            prices=prices,
            photo_url=order.cafe.logo.url if order.cafe.logo else None,
            need_shipping=order.delivery_type == 'delivery',
        )
        
        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'order_number': order.order_number,
            'total_amount': float(order.total_amount),
            'payment_id': payment.id,
            'message': 'Инвойс отправлен в Telegram'
        })
        
    except Exception as e:
        logger.error(f"Ошибка создания платежа: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Внутренняя ошибка сервера'
        }, status=500)



@csrf_exempt
@require_http_methods(["GET"])
def payment_status(request, payment_id):
    """Проверка статуса платежа"""
    try:
        from payments.models import Payment
        
        payment = Payment.objects.get(id=payment_id)
        
        return JsonResponse({
            'success': True,
            'payment_id': payment.id,
            'status': payment.status,
            'order_number': payment.order.order_number,
            'amount': float(payment.amount),
            'created_at': payment.created_at.isoformat(),
            'paid_at': payment.paid_at.isoformat() if payment.paid_at else None,
        })
        
    except Payment.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Платеж не найден'
        }, status=404)
    except Exception as e:
        logger.error(f"Ошибка проверки статуса платежа: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Внутренняя ошибка сервера'
        }, status=500)