from django.contrib import admin
from .models import TelegramUser


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'username', 'telegram_id', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'language_code', 'created_at']
    search_fields = ['first_name', 'last_name', 'username', 'telegram_id', 'phone']
    readonly_fields = ['telegram_id', 'created_at', 'updated_at', 'last_activity']
    
    fieldsets = (
        ('Telegram информация', {
            'fields': ('telegram_id', 'username', 'first_name', 'last_name')
        }),
        ('Контактная информация', {
            'fields': ('phone',)
        }),
        ('Настройки', {
            'fields': ('is_active', 'language_code')
        }),
        ('Django интеграция', {
            'fields': ('user',)
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at', 'last_activity'),
            'classes': ('collapse',)
        }),
    )
