import json
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from .models import Payment

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class YooKassaWebhookView(View):
    """Обработчик webhook'ов от ЮKassa"""
    
    def post(self, request):
        try:
            # Получаем данные из запроса
            webhook_data = json.loads(request.body.decode('utf-8'))
            
            logger.info(f"Получен webhook от ЮKassa: {webhook_data}")
            
            # Извлекаем информацию о событии
            event_type = webhook_data.get('event')
            payment_data = webhook_data.get('object', {})
            payment_id = payment_data.get('id')
            
            if not payment_id:
                logger.warning("Webhook без payment_id")
                return HttpResponse(status=400)
            
            # Обрабатываем разные типы событий
            if event_type == 'payment.succeeded':
                self.handle_payment_succeeded(payment_data)
            elif event_type == 'payment.canceled':
                self.handle_payment_canceled(payment_data)
            elif event_type == 'payment.waiting_for_capture':
                self.handle_payment_waiting_for_capture(payment_data)
            elif event_type == 'refund.succeeded':
                self.handle_refund_succeeded(payment_data)
            else:
                logger.info(f"Неизвестный тип события: {event_type}")
            
            return HttpResponse(status=200)
            
        except Exception as e:
            logger.error(f"Ошибка обработки webhook: {e}")
            return HttpResponse(status=500)
    
    def handle_payment_succeeded(self, payment_data):
        """Обработка успешного платежа"""
        payment_id = payment_data.get('id')
        amount = payment_data.get('amount', {}).get('value')
        
        try:
            # Находим платеж по external_payment_id
            payment = Payment.objects.get(external_payment_id=payment_id)
            
            if payment.status != 'completed':
                payment.status = 'completed'
                payment.provider_payment_charge_id = payment_id
                payment.save()
                
                # Обновляем статус заказа
                payment.order.status = 'confirmed'
                payment.order.save()
                
                logger.info(f"Платеж {payment_id} успешно обработан")
            
        except Payment.DoesNotExist:
            logger.warning(f"Платеж с ID {payment_id} не найден")
    
    def handle_payment_canceled(self, payment_data):
        """Обработка отмененного платежа"""
        payment_id = payment_data.get('id')
        
        try:
            payment = Payment.objects.get(external_payment_id=payment_id)
            payment.status = 'failed'
            payment.save()
            
            logger.info(f"Платеж {payment_id} отменен")
            
        except Payment.DoesNotExist:
            logger.warning(f"Платеж с ID {payment_id} не найден")
    
    def handle_payment_waiting_for_capture(self, payment_data):
        """Обработка платежа, ожидающего подтверждения"""
        payment_id = payment_data.get('id') 
        
        try:
            payment = Payment.objects.get(external_payment_id=payment_id)
            payment.status = 'processing'
            payment.save()
            
            logger.info(f"Платеж {payment_id} ожидает подтверждения")
            
        except Payment.DoesNotExist:
            logger.warning(f"Платеж с ID {payment_id} не найден")
    
    def handle_refund_succeeded(self, payment_data):
        """Обработка успешного возврата"""
        payment_id = payment_data.get('id')
        
        logger.info(f"Получен возврат для платежа {payment_id}")
        # Здесь можно добавить логику обработки возвратов
