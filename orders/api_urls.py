"""
URL configuration for orders API
"""
from django.urls import path
from .api_views import create_payment, payment_status

app_name = 'orders_api'

urlpatterns = [
    path('create-payment/', create_payment, name='create_payment'),
    path('payment-status/<int:payment_id>/', payment_status, name='payment_status'),
]