"""
Middleware для автоматической авторизации через Telegram WebApp
"""
import json
import urllib.parse
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import JsonResponse
from users.models import TelegramUser
from users.telegram_auth import get_telegram_auth


class TelegramWebAppAuthMiddleware:
    """
    Middleware для автоматической авторизации пользователей через Telegram WebApp
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Проверяем авторизацию только если пользователь не авторизован
        if not request.user.is_authenticated:
            self._try_telegram_auth(request)
        
        response = self.get_response(request)
        return response

    def _try_telegram_auth(self, request):
        """Попытка авторизации через Telegram WebApp данные"""
        try:
            # Пропускаем AJAX запросы к корзине чтобы не мешать им
            if request.path.startswith('/add-to-cart/') or request.path.startswith('/cart/'):
                return
            # Проверяем наличие Telegram WebApp данных в заголовках или параметрах
            init_data = None
            
            # Способ 1: из заголовка Authorization
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('tma '):
                init_data = auth_header[4:]  # убираем 'tma '
            
            # Способ 2: из GET параметров (для тестирования)
            elif 'tgWebAppData' in request.GET:
                init_data = request.GET.get('tgWebAppData')
            
            # Способ 3: из POST данных
            elif request.method == 'POST' and request.content_type == 'application/json':
                try:
                    body = json.loads(request.body)
                    init_data = body.get('_auth')
                except:
                    pass
            
            # Способ 4: из заголовка X-Telegram-Init-Data
            elif 'HTTP_X_TELEGRAM_INIT_DATA' in request.META:
                init_data = request.META.get('HTTP_X_TELEGRAM_INIT_DATA')
            
            if not init_data:
                return
            
            # Валидируем данные
            telegram_auth = get_telegram_auth()
            validated_data = telegram_auth.validate_init_data(init_data)
            
            if not validated_data:
                return
            
            user_info = validated_data.get('user', {})
            telegram_id = user_info.get('id')
            
            if not telegram_id:
                return
            
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
            
        except Exception as e:
            # В случае ошибки просто не авторизуем пользователя
            # Логируем ошибку для отладки
            print(f"Ошибка автоавторизации Telegram: {e}")
            pass