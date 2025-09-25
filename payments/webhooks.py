"""
Webhook для обработки уведомлений от ЮKassa
"""
import json
import logging
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from django.conf import settings
from payments.models import Payment
from payments.yookassa_service import YooKassaService

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class YookassaWebhookView(View):
    """Обработчик webhook'ов от ЮKassa"""
    
    def post(self, request):
        """Обрабатывает уведомления от ЮKassa"""
        try:
            # Получаем данные из запроса
            raw_data = request.body.decode('utf-8')
            data = json.loads(raw_data)
            
            logger.info(f"Получен webhook от ЮKassa: {data}")
            
            # Инициализируем сервис ЮKassa
            yookassa_service = YooKassaService()
            
            # Обрабатываем данные webhook'а
            processed_data = yookassa_service.process_webhook_data(data)
            
            if not processed_data:
                logger.error("Не удалось обработать данные webhook'а")
                return HttpResponseBadRequest("Invalid webhook data")
            
            # Извлекаем данные
            event_type = processed_data['event_type']
            payment_id = processed_data['payment_id']
            status = processed_data['status']
            
            logger.info(f"Событие: {event_type}, Платеж: {payment_id}, Статус: {status}")
            
            # Ищем платеж в нашей базе данных
            payment = self._find_payment(payment_id, processed_data)
            
            if not payment:
                logger.warning(f"Платеж с ID {payment_id} не найден в базе данных")
                # Возвращаем 200, чтобы ЮKassa не повторяла запрос
                return HttpResponse("Payment not found", status=200)
            
            # Обрабатываем событие
            self._handle_webhook_event(payment, processed_data)
            
            logger.info(f"Webhook успешно обработан для платежа {payment_id}")
            return HttpResponse("OK")
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            return HttpResponseBadRequest("Invalid JSON")
        except Exception as e:
            logger.error(f"Ошибка обработки webhook'а: {e}")
            return HttpResponse("Internal Server Error", status=500)
    
    def _find_payment(self, payment_id: str, processed_data: dict):
        """Найти платеж в базе данных"""
        # Сначала ищем по external_payment_id
        payment = Payment.objects.filter(external_payment_id=payment_id).first()
        
        if payment:
            return payment
        
        # Если не найден, ищем по provider_payment_charge_id
        payment = Payment.objects.filter(provider_payment_charge_id=payment_id).first()
        
        if payment:
            return payment
        
        # Если не найден, ищем по metadata (может содержать invoice_payload)
        metadata = processed_data.get('metadata', {})
        invoice_payload = metadata.get('invoice_payload')
        
        if invoice_payload:
            payment = Payment.objects.filter(invoice_payload=invoice_payload).first()
            if payment:
                # Сохраняем payment_id для будущих webhook'ов
                payment.external_payment_id = payment_id
                payment.save(update_fields=['external_payment_id'])
                return payment
        
        return None
    
    def _handle_webhook_event(self, payment, processed_data: dict):
        """Обработать событие webhook'а"""
        event_type = processed_data['event_type']
        status = processed_data['status']
        
        logger.info(f"Обработка события {event_type} для заказа #{payment.order.order_number}")
        
        # Обновляем external_payment_id если его не было
        if not payment.external_payment_id:
            payment.external_payment_id = processed_data['payment_id']
        
        if event_type == 'payment.succeeded' and status == 'succeeded':
            # Платеж успешно завершен
            self._handle_successful_payment(payment, processed_data)
            
        elif event_type == 'payment.canceled' or status == 'canceled':
            # Платеж отменен
            self._handle_canceled_payment(payment, processed_data)
            
        elif event_type == 'payment.waiting_for_capture':
            # Платеж ожидает подтверждения
            self._handle_waiting_payment(payment, processed_data)
            
        else:
            logger.info(f"Событие {event_type} ({status}) не требует обработки")
        
        # Сохраняем изменения
        payment.save()
    
    def _handle_successful_payment(self, payment, processed_data: dict):
        """Обработать успешный платеж"""
        logger.info(f"Платеж успешно завершен для заказа #{payment.order.order_number}")
        
        payment.status = 'completed'
        payment.paid_at = timezone.now()
        
        # Сохраняем данные о платеже
        if processed_data.get('captured_at'):
            try:
                payment.paid_at = timezone.fromisoformat(
                    processed_data['captured_at'].replace('Z', '+00:00')
                )
            except ValueError:
                pass  # Используем текущее время если не удалось распарсить
        
        # Обновляем заказ
        payment.order.status = 'confirmed'
        payment.order.save(update_fields=['status'])
        
        # Отправляем уведомление пользователю в Telegram
        self._send_payment_notification_to_user(payment.order)
        
        # Отправляем уведомление персоналу
        self._notify_staff_about_order(payment.order)
        
        logger.info(f"Заказ #{payment.order.order_number} помечен как оплаченный")
    
    def _handle_canceled_payment(self, payment, processed_data: dict):
        """Обработать отмененный платеж"""
        logger.info(f"Платеж отменен для заказа #{payment.order.order_number}")
        
        payment.status = 'cancelled'
        
        # Обновляем заказ
        payment.order.status = 'cancelled'
        payment.order.save(update_fields=['status'])
    
    def _handle_waiting_payment(self, payment, processed_data: dict):
        """Обработать платеж, ожидающий подтверждения"""
        logger.info(f"Платеж ожидает подтверждения для заказа #{payment.order.order_number}")
        
        payment.status = 'processing'
    
    def _send_payment_notification_to_user(self, order):
        """Отправить уведомление пользователю в Telegram о успешной оплате"""
        try:
            # Проверяем, что у пользователя есть telegram_id
            if order.user.telegram_id and order.user.telegram_id != 0:
                import requests
                
                # Используем основной бот для отправки уведомления пользователю
                bot_token = settings.TELEGRAM_BOT_TOKEN
                
                message = (
                    f"✅ *Платеж успешен!*\n"
                    f"Номер заказа: *#{order.order_number}*\n"
                    f"Сумма: {order.total_amount} ₽\n"
                    f"Спасибо за покупку! 🎉\n\n"
                    f"📋 Ваш заказ передан в кафе и готовится.\n"
                    f"🔔 Вы получите уведомление, когда заказ будет готов.\n\n"
                    f"🏪 Кафе: {order.cafe.name}\n"
                    f"📍 {order.cafe.address}\n\n"
                    f"👆 *Посмотреть ваш заказ вы можете в приложении*"
                )
                
                # Отправляем сообщение через HTTP API
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    'chat_id': order.user.telegram_id,
                    'text': message,
                    'parse_mode': 'Markdown'
                }
                
                response = requests.post(url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('ok'):
                        logger.info(f"Уведомление о платеже отправлено пользователю {order.user.telegram_id}")
                    else:
                        logger.error(f"Telegram API ошибка: {result.get('description', 'Unknown error')}")
                else:
                    logger.error(f"HTTP ошибка при отправке уведомления: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления пользователю: {e}")
    
    def _notify_staff_about_order(self, order):
        """Отправить уведомление персоналу о новом заказе"""
        try:
            from orders.staff_notifications import staff_notification_service
            staff_notification_service.send_new_order_notification_sync(order)
            logger.info(f"Уведомление персонала отправлено для заказа #{order.order_number}")
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления персоналу: {e}")


# Создаем экземпляр view для использования в urls.py
yookassa_webhook = YookassaWebhookView.as_view()