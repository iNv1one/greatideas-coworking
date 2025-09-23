from django.db import models
from users.models import TelegramUser
from cafes.models import Cafe


class BotMessage(models.Model):
    """Сообщения бота для логирования"""
    
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, verbose_name="Пользователь")
    message_type = models.CharField(max_length=50, verbose_name="Тип сообщения")
    message_text = models.TextField(verbose_name="Текст сообщения")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Отправлено")
    
    class Meta:
        verbose_name = "Сообщение бота"
        verbose_name_plural = "Сообщения бота"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.first_name} - {self.message_type}"


class UserSession(models.Model):
    """Сессии пользователей для отслеживания состояния"""
    
    user = models.OneToOneField(TelegramUser, on_delete=models.CASCADE, verbose_name="Пользователь")
    current_cafe = models.ForeignKey(
        Cafe, on_delete=models.SET_NULL, null=True, blank=True, 
        verbose_name="Текущее кафе"
    )
    current_step = models.CharField(max_length=100, blank=True, verbose_name="Текущий шаг")
    session_data = models.JSONField(default=dict, verbose_name="Данные сессии")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Пользовательская сессия"
        verbose_name_plural = "Пользовательские сессии"
    
    def __str__(self):
        return f"Сессия {self.user.first_name}"
