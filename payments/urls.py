"""
URLs для payments приложения
"""
from django.urls import path
from .webhooks import yookassa_webhook

app_name = 'payments'

urlpatterns = [
    path('yookassa/webhook/', yookassa_webhook, name='yookassa_webhook'),
]