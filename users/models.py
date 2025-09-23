from django.db import models
from django.contrib.auth.models import User


class TelegramUser(models.Model):
    """Пользователи из Telegram"""
    
    telegram_id = models.BigIntegerField(unique=True, verbose_name="Telegram ID")
    username = models.CharField(max_length=150, blank=True, verbose_name="Username")
    first_name = models.CharField(max_length=150, verbose_name="Имя")
    last_name = models.CharField(max_length=150, blank=True, verbose_name="Фамилия")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    
    # Связь с Django User (опционально)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True, 
        verbose_name="Пользователь Django"
    )
    
    # Настройки
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    language_code = models.CharField(max_length=10, default='ru', verbose_name="Язык")
    
    # Для Web App авторизации
    allows_write_to_pm = models.BooleanField(default=False, verbose_name="Разрешает писать в ЛС")
    
    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Регистрация")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    last_activity = models.DateTimeField(auto_now=True, verbose_name="Последняя активность")
    
    class Meta:
        verbose_name = "Telegram пользователь"
        verbose_name_plural = "Telegram пользователи"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} ({self.telegram_id})"
    
    @property
    def full_name(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
