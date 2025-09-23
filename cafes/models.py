from django.db import models
from django.core.validators import RegexValidator


class Cafe(models.Model):
    """Модель для представления кафе"""
    
    name = models.CharField(max_length=200, verbose_name="Название кафе")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="URL-slug")
    description = models.TextField(blank=True, verbose_name="Описание")
    address = models.CharField(max_length=300, verbose_name="Адрес")
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Номер телефона должен быть в формате: '+999999999'. До 15 цифр."
    )
    phone = models.CharField(validators=[phone_regex], max_length=17, verbose_name="Телефон")
    
    # Режим работы
    working_hours = models.CharField(max_length=200, verbose_name="Режим работы")
    
    # Изображения
    logo = models.ImageField(upload_to='cafes/logos/', blank=True, verbose_name="Логотип")
    cover_image = models.ImageField(upload_to='cafes/covers/', blank=True, verbose_name="Обложка")
    
    # Настройки
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    min_order_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Минимальная сумма заказа"
    )
    delivery_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Стоимость доставки"
    )
    
    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    
    class Meta:
        verbose_name = "Кафе"
        verbose_name_plural = "Кафе"
        ordering = ['name']
    
    def __str__(self):
        return self.name
