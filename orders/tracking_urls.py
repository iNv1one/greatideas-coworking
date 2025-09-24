"""
URL маршруты для отслеживания заказов
"""
from django.urls import path
from . import tracking_views

urlpatterns = [
    # Отслеживание конкретного заказа
    path('status/<str:order_number>/', tracking_views.order_status, name='order_status'),
    
    # API для получения статуса заказа
    path('api/status/<str:order_number>/', tracking_views.api_order_status, name='api_order_status'),
    
    # Список заказов пользователя
    path('my-orders/', tracking_views.user_orders, name='user_orders'),
]