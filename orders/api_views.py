"""
API views для работы с платежами
"""
import json
import logging
import asyncio
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from telegram import Bot
from users.models import TelegramUser
from orders.telegram_payments import TelegramPaymentService

logger = logging.getLogger(__name__)


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
        
        # Создаем сервис платежей
        payment_service = TelegramPaymentService()
        
        # Создаем заказ
        order = payment_service.create_order_from_cart(
            telegram_user=telegram_user,
            cart_data=cart_data,
            delivery_type=data.get('delivery_type', 'pickup'),
            customer_name=data.get('customer_name', ''),
            customer_phone=data.get('customer_phone', ''),
            delivery_address=data.get('delivery_address', ''),
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