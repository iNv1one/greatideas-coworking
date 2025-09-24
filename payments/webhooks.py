"""
Webhook для обработки уведомлений от ЮKassa
"""
import json
import logging
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from payments.models import Payment

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class YookassaWebhookView(View):
    """Обработчик webhook'ов от ЮKassa"""
    
    def post(self, request):
        """Обрабатывает уведомления от ЮKassa"""
        try:
            # Получаем данные из запроса
            data = json.loads(request.body)
            logger.info(f"Получен webhook от ЮKassa: {data}")
            
            # Извлекаем информацию о событии
            event_type = data.get('event')
            payment_object = data.get('object', {})
            payment_id = payment_object.get('id')
            status = payment_object.get('status')
            
            logger.info(f"Событие: {event_type}, Платеж: {payment_id}, Статус: {status}")
            
            if not payment_id:
                logger.error("Отсутствует ID платежа в webhook")
                return HttpResponseBadRequest("Missing payment ID")
            
            # Ищем платеж в нашей базе данных
            try:
                # Ищем по external_payment_id или provider_payment_charge_id
                payment = Payment.objects.filter(
                    external_payment_id=payment_id
                ).first()
                
                if not payment:
                    # Если не найден, попробуем по другим полям
                    payment = Payment.objects.filter(
                        provider_payment_charge_id=payment_id
                    ).first()
                
                if not payment:
                    logger.warning(f"Платеж {payment_id} не найден в базе данных")
                    return HttpResponse("Payment not found", status=404)
                    
            except Exception as e:
                logger.error(f"Ошибка поиска платежа {payment_id}: {e}")
                return HttpResponseBadRequest("Database error")
            
            # Обрабатываем разные типы событий
            if event_type == 'payment.succeeded':
                logger.info(f"Платеж {payment_id} успешно оплачен")
                self._handle_payment_succeeded(payment, payment_object)
                
            elif event_type == 'payment.canceled':
                logger.info(f"Платеж {payment_id} отменен")
                self._handle_payment_canceled(payment, payment_object)
                
            elif event_type == 'payment.waiting_for_capture':
                logger.info(f"Платеж {payment_id} ожидает подтверждения")
                self._handle_payment_waiting_for_capture(payment, payment_object)
                
            elif event_type == 'refund.succeeded':
                logger.info(f"Возврат по платежу {payment_id} успешно выполнен")
                self._handle_refund_succeeded(payment, payment_object)
                
            else:
                logger.warning(f"Неизвестный тип события: {event_type}")
            
            return HttpResponse("OK")
            
        except json.JSONDecodeError:
            logger.error("Неверный JSON в webhook запросе")
            return HttpResponseBadRequest("Invalid JSON")
            
        except Exception as e:
            logger.error(f"Ошибка обработки webhook: {e}")
            return HttpResponseBadRequest("Internal error")
    
    def _handle_payment_succeeded(self, payment: Payment, payment_data: dict):
        """Обрабатывает успешный платеж"""
        try:
            # Обновляем статус платежа
            payment.status = 'completed'
            payment.external_payment_id = payment_data.get('id')
            payment.provider_payment_charge_id = payment_data.get('id')
            
            # Сохраняем дополнительные данные
            if 'paid_at' in payment_data:
                from django.utils.dateparse import parse_datetime
                payment.paid_at = parse_datetime(payment_data['paid_at'])
            
            payment.save()
            
            # Обновляем статус заказа
            order = payment.order
            if order.status == 'pending':
                order.status = 'confirmed'
                order.save()
                logger.info(f"Заказ {order.order_number} подтвержден")
            
        except Exception as e:
            logger.error(f"Ошибка обработки успешного платежа: {e}")
    
    def _handle_payment_canceled(self, payment: Payment, payment_data: dict):
        """Обрабатывает отмененный платеж"""
        try:
            payment.status = 'failed'
            payment.save()
            
            # Можно также обновить статус заказа
            order = payment.order
            if order.status == 'pending':
                order.status = 'cancelled'
                order.save()
                logger.info(f"Заказ {order.order_number} отменен")
                
        except Exception as e:
            logger.error(f"Ошибка обработки отмененного платежа: {e}")
    
    def _handle_payment_waiting_for_capture(self, payment: Payment, payment_data: dict):
        """Обрабатывает платеж, ожидающий подтверждения"""
        try:
            payment.status = 'processing'
            payment.external_payment_id = payment_data.get('id')
            payment.save()
            logger.info(f"Платеж {payment.id} ожидает подтверждения")
            
        except Exception as e:
            logger.error(f"Ошибка обработки платежа в ожидании: {e}")
    
    def _handle_refund_succeeded(self, payment: Payment, payment_data: dict):
        """Обрабатывает успешный возврат"""
        try:
            payment.status = 'refunded'
            payment.save()
            logger.info(f"Возврат по платежу {payment.id} выполнен")
            
        except Exception as e:
            logger.error(f"Ошибка обработки возврата: {e}")


# Функция-обертка для использования без класса
@csrf_exempt
@require_http_methods(["POST"])
def yookassa_webhook(request):
    """Простая функция-обработчик webhook'а"""
    view = YookassaWebhookView()
    return view.post(request)