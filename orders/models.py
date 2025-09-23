from django.db import models
from django.utils import timezone
from cafes.models import Cafe
from menu.models import MenuItem, MenuItemVariant, Addon
from users.models import TelegramUser


class Order(models.Model):
    """Заказы пользователей"""
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтвержден'),
        ('preparing', 'Готовится'),
        ('ready', 'Готов'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]
    
    DELIVERY_CHOICES = [
        ('pickup', 'Самовывоз'),
        ('delivery', 'Доставка'),
    ]
    
    # Основная информация
    cafe = models.ForeignKey(Cafe, on_delete=models.CASCADE, verbose_name="Кафе")
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, verbose_name="Пользователь")
    
    # Номер заказа
    order_number = models.CharField(max_length=20, unique=True, verbose_name="Номер заказа")
    
    # Статус и тип доставки
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default='pickup', verbose_name="Тип получения")
    
    # Сумма заказа
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая сумма")
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Стоимость доставки")
    
    # Контактная информация
    customer_name = models.CharField(max_length=200, verbose_name="Имя клиента")
    customer_phone = models.CharField(max_length=20, verbose_name="Телефон клиента")
    delivery_address = models.TextField(blank=True, verbose_name="Адрес доставки")
    
    # Дополнительная информация
    comment = models.TextField(blank=True, verbose_name="Комментарий к заказу")
    
    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="Доставлен")
    
    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Заказ #{self.order_number} - {self.cafe.name}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Генерируем номер заказа
            today = timezone.now().strftime('%Y%m%d')
            last_order = Order.objects.filter(
                created_at__date=timezone.now().date()
            ).order_by('-id').first()
            
            if last_order and last_order.order_number.startswith(today):
                sequence = int(last_order.order_number[-3:]) + 1
            else:
                sequence = 1
            
            self.order_number = f"{today}{sequence:03d}"
        
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """Позиции в заказе"""
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Заказ")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, verbose_name="Позиция меню")
    variant = models.ForeignKey(MenuItemVariant, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Вариант размера")
    
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Базовая цена")
    variant_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Цена варианта")
    addons_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Цена добавок")
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Итоговая цена за единицу")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая стоимость")
    
    # Комментарий к позиции (например, "без лука")
    comment = models.CharField(max_length=500, blank=True, verbose_name="Комментарий")
    
    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"
    
    def __str__(self):
        variant_info = f" ({self.variant.name})" if self.variant else ""
        return f"{self.menu_item.name}{variant_info} x{self.quantity}"
    
    def save(self, *args, **kwargs):
        # Вычисляем итоговую цену
        if self.base_price is None:
            self.base_price = self.menu_item.price
        
        self.variant_price = self.variant.price_modifier if self.variant else 0
        
        # Сначала сохраняем объект, чтобы можно было получить связанные добавки
        if self.pk:
            addons_total = sum(item.addon.price for item in self.selected_addons.all())
            self.addons_price = addons_total
        
        if self.final_price is None:
            self.final_price = self.base_price + self.variant_price + self.addons_price
        
        self.total_price = self.final_price * self.quantity
        
        super().save(*args, **kwargs)
    
    def get_display_name(self):
        """Получить отображаемое имя с вариантом"""
        if self.variant:
            return f"{self.menu_item.name} ({self.variant.name})"
        return self.menu_item.name
    
    def get_addons_list(self):
        """Получить список выбранных добавок"""
        return [item.addon for item in self.selected_addons.all()]


class OrderItemAddon(models.Model):
    """Добавки к позициям заказа"""
    
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='selected_addons', verbose_name="Позиция заказа")
    addon = models.ForeignKey(Addon, on_delete=models.CASCADE, verbose_name="Добавка")
    
    class Meta:
        verbose_name = "Добавка к позиции"
        verbose_name_plural = "Добавки к позициям"
        unique_together = ['order_item', 'addon']
    
    def __str__(self):
        return f"{self.order_item} - {self.addon.name}"
