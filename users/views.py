import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.conf import settings
from orders.models import Order
from users.models import TelegramUser
from .telegram_auth import get_telegram_auth

def profile(request):
    """
    Страница профиля пользователя с историей заказов
    """
    orders = []
    user_info = None
    
    if request.user.is_authenticated:
        # Для демонстрации показываем информацию о пользователе
        user_info = {
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'date_joined': request.user.date_joined,
        }
        
        # Пытаемся найти связанного TelegramUser
        try:
            # Ищем TelegramUser по связанному Django пользователю
            telegram_user = TelegramUser.objects.filter(user=request.user).first()
            
            if telegram_user:
                orders = Order.objects.filter(user=telegram_user).order_by('-created_at')[:10]
        except Exception as e:
            # Если возникла ошибка, просто не показываем заказы
            print(f"Error fetching orders: {e}")
            orders = []
    
    context = {
        'user_info': user_info,
        'orders': orders,
    }
    return render(request, 'users/profile.html', context)


def telegram_login_view(request):
    """Страница входа через Telegram"""
    context = {
        'bot_username': getattr(settings, 'TELEGRAM_BOT_USERNAME', ''),
        'webapp_url': request.build_absolute_uri('/'),
    }
    return render(request, 'users/telegram_login.html', context)


@csrf_exempt
def telegram_auth_callback(request):
    """Обработка данных авторизации от Telegram Web App"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Только POST запросы'}, status=405)
    
    try:
        # Получаем данные от Telegram
        data = json.loads(request.body)
        init_data = data.get('initData')
        
        if not init_data:
            return JsonResponse({'error': 'initData отсутствует'}, status=400)
        
        # Валидируем данные
        telegram_auth = get_telegram_auth()
        validated_data = telegram_auth.validate_init_data(init_data)
        
        if not validated_data:
            return JsonResponse({'error': 'Невалидные данные авторизации'}, status=400)
        
        user_info = validated_data.get('user', {})
        telegram_id = user_info.get('id')
        
        if not telegram_id:
            return JsonResponse({'error': 'ID пользователя отсутствует'}, status=400)
        
        # Находим или создаем пользователя Telegram
        telegram_user, created = TelegramUser.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                'username': user_info.get('username', ''),
                'first_name': user_info.get('first_name', ''),
                'last_name': user_info.get('last_name', ''),
                'language_code': user_info.get('language_code', 'ru'),
                'allows_write_to_pm': validated_data.get('allows_write_to_pm', False),
            }
        )
        
        # Если пользователь уже существует, обновляем данные
        if not created:
            telegram_user.username = user_info.get('username', telegram_user.username)
            telegram_user.first_name = user_info.get('first_name', telegram_user.first_name)
            telegram_user.last_name = user_info.get('last_name', telegram_user.last_name)
            telegram_user.language_code = user_info.get('language_code', telegram_user.language_code)
            telegram_user.allows_write_to_pm = validated_data.get('allows_write_to_pm', telegram_user.allows_write_to_pm)
            telegram_user.save()
        
        # Создаем или получаем Django пользователя
        if not telegram_user.user:
            # Создаем нового Django пользователя
            username = f"tg_{telegram_id}"
            django_user = User.objects.create_user(
                username=username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
            )
            telegram_user.user = django_user
            telegram_user.save()
        else:
            # Обновляем существующего Django пользователя
            django_user = telegram_user.user
            django_user.first_name = telegram_user.first_name
            django_user.last_name = telegram_user.last_name
            django_user.save()
        
        # Авторизуем пользователя в Django
        login(request, django_user)
        
        return JsonResponse({
            'success': True,
            'user': {
                'id': django_user.id,
                'username': django_user.username,
                'first_name': django_user.first_name,
                'last_name': django_user.last_name,
                'telegram_id': telegram_user.telegram_id,
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат JSON'}, status=400)
    except Exception as e:
        print(f"Ошибка авторизации Telegram: {e}")
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)
