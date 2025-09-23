from django.contrib import admin
from .models import BotMessage, UserSession


@admin.register(BotMessage)
class BotMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'message_type', 'created_at']
    list_filter = ['message_type', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'message_text']
    readonly_fields = ['created_at']


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_cafe', 'current_step', 'updated_at']
    list_filter = ['current_cafe', 'created_at']
    search_fields = ['user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
