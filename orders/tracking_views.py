"""
Views для отслеживания заказов пользователями
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from orders.models import Order
from users.models import TelegramUser


def order_status(request, order_number):
    """Страница отслеживания статуса заказа"""
    order = get_object_or_404(Order, order_number=order_number)
    
    # Проверяем права доступа (только владелец заказа может его видеть)
    if hasattr(request.user, 'telegram_user'):
        if order.user != request.user.telegram_user:
            return render(request, 'orders/access_denied.html')
    
    context = {
        'order': order,
        'status_display': order.get_status_display(),
        'can_track': True,
    }
    
    return render(request, 'orders/order_status.html', context)


def api_order_status(request, order_number):
    """API для получения статуса заказа"""
    try:
        order = Order.objects.get(order_number=order_number)
        
        status_info = {
            'order_number': order.order_number,
            'status': order.status,
            'status_display': order.get_status_display(),
            'created_at': order.created_at.isoformat(),
            'cafe_name': order.cafe.name,
            'cafe_address': order.cafe.address,
            'total_amount': float(order.total_amount),
            'delivery_type': order.delivery_type,
            'delivery_type_display': order.get_delivery_type_display(),
        }
        
        # Добавляем время доставки если заказ доставлен
        if order.delivered_at:
            status_info['delivered_at'] = order.delivered_at.isoformat()
        
        # Статус этапы для отображения прогресса
        status_steps = [
            {
                'key': 'pending',
                'title': 'Ожидает подтверждения',
                'completed': order.status in ['confirmed', 'preparing', 'ready', 'delivered'],
                'active': order.status == 'pending'
            },
            {
                'key': 'confirmed',
                'title': 'Подтвержден',
                'completed': order.status in ['preparing', 'ready', 'delivered'],
                'active': order.status == 'confirmed'
            },
            {
                'key': 'preparing',
                'title': 'Готовится',
                'completed': order.status in ['ready', 'delivered'],
                'active': order.status == 'preparing'
            },
            {
                'key': 'ready',
                'title': 'Готов к выдаче' if order.delivery_type == 'pickup' else 'Готов к доставке',
                'completed': order.status == 'delivered',
                'active': order.status == 'ready'
            },
            {
                'key': 'delivered',
                'title': 'Выдан' if order.delivery_type == 'pickup' else 'Доставлен',
                'completed': order.status == 'delivered',
                'active': order.status == 'delivered'
            }
        ]
        
        status_info['steps'] = status_steps
        
        return JsonResponse({
            'success': True,
            'order': status_info
        })
        
    except Order.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Заказ не найден'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Произошла ошибка при получении статуса заказа'
        }, status=500)


def user_orders(request):
    """Список заказов пользователя"""
    if not hasattr(request.user, 'telegram_user'):
        return render(request, 'orders/no_orders.html')
    
    orders = Order.objects.filter(
        user=request.user.telegram_user
    ).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    
    return render(request, 'orders/user_orders.html', context)