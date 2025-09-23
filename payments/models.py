from django.db import models
from django.utils import timezone
from orders.models import Order


class Payment(models.Model):
    """Платежи по заказам"""
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('processing', 'Обрабатывается'),
        ('completed', 'Завершен'),
        ('failed', 'Неудачно'),
        ('cancelled', 'Отменен'),
        ('refunded', 'Возврат'),
    ]
    
    METHOD_CHOICES = [
        ('telegram', 'Telegram Payments'),
        ('card', 'Банковская карта'),
        ('cash', 'Наличные'),
        ('online', 'Онлайн-платеж'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, verbose_name="Заказ", related_name='payment')
    
    # Информация о платеже
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='telegram', verbose_name="Способ оплаты")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    
    # Внешние идентификаторы
    external_payment_id = models.CharField(max_length=200, blank=True, verbose_name="ID внешнего платежа")
    provider_payment_charge_id = models.CharField(max_length=200, blank=True, verbose_name="ID провайдера")
    
    # Telegram-специфичные поля
    telegram_payment_charge_id = models.CharField(max_length=255, blank=True, verbose_name="ID платежа Telegram")
    invoice_payload = models.CharField(max_length=255, blank=True, verbose_name="Payload инвойса")
    shipping_option_id = models.CharField(max_length=255, blank=True, verbose_name="ID способа доставки")
    
    # Дополнительная информация
    currency = models.CharField(max_length=3, default='RUB', verbose_name="Валюта")
    description = models.TextField(blank=True, verbose_name="Описание")
    
    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="Оплачен")
    
    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Платеж {self.order.order_number} - {self.amount} {self.currency}"
    
    def mark_as_paid(self, telegram_charge_id=None, provider_charge_id=None):
        """Отметить платеж как оплаченный"""
        self.status = 'completed'
        if telegram_charge_id:
            self.telegram_payment_charge_id = telegram_charge_id
        if provider_charge_id:
            self.provider_payment_charge_id = provider_charge_id
        self.paid_at = timezone.now()
        self.save()
        
        # Обновляем статус заказа
        self.order.status = 'confirmed'
        self.order.save()
