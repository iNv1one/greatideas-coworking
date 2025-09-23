import hashlib
import hmac
import json
import urllib.parse
from datetime import datetime, timedelta
from django.conf import settings
from typing import Dict, Optional


class TelegramWebAppAuth:
    """Класс для работы с авторизацией через Telegram Web App"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
    
    def validate_init_data(self, init_data: str) -> Dict:
        """
        Проверяет подлинность данных от Telegram Web App
        
        Args:
            init_data: строка с данными инициализации от Telegram
            
        Returns:
            dict: проверенные данные пользователя или None если данные невалидны
        """
        try:
            # Парсим данные
            parsed_data = urllib.parse.parse_qs(init_data)
            
            # Извлекаем hash
            received_hash = parsed_data.get('hash', [None])[0]
            if not received_hash:
                raise ValueError("Hash отсутствует")
            
            # Удаляем hash из данных для проверки
            data_check_string_parts = []
            for key, values in parsed_data.items():
                if key != 'hash':
                    data_check_string_parts.append(f"{key}={values[0]}")
            
            # Сортируем по ключам
            data_check_string_parts.sort()
            data_check_string = '\n'.join(data_check_string_parts)
            
            # Создаем секретный ключ
            secret_key = hmac.new(
                b"WebAppData", 
                self.bot_token.encode('utf-8'), 
                hashlib.sha256
            ).digest()
            
            # Вычисляем hash
            calculated_hash = hmac.new(
                secret_key,
                data_check_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Проверяем hash
            if not hmac.compare_digest(received_hash, calculated_hash):
                raise ValueError("Неверный hash")
            
            # Проверяем время (данные должны быть не старше 1 часа)
            auth_date = parsed_data.get('auth_date', [None])[0]
            if auth_date:
                auth_time = datetime.fromtimestamp(int(auth_date))
                if datetime.now() - auth_time > timedelta(hours=1):
                    raise ValueError("Данные устарели")
            
            # Парсим данные пользователя
            user_data = parsed_data.get('user', [None])[0]
            if user_data:
                user_info = json.loads(user_data)
                return {
                    'user': user_info,
                    'auth_date': auth_date,
                    'query_id': parsed_data.get('query_id', [None])[0],
                    'allows_write_to_pm': parsed_data.get('allows_write_to_pm', [False])[0] == 'true'
                }
            
            return {}
            
        except Exception as e:
            print(f"Ошибка валидации Telegram Web App данных: {e}")
            return None
    
    def create_auth_url(self, webapp_url: str) -> str:
        """
        Создает URL для авторизации через Telegram Web App
        """
        return f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?startapp={webapp_url}"


def get_telegram_auth() -> TelegramWebAppAuth:
    """Получить экземпляр класса авторизации"""
    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN не настроен в settings")
    return TelegramWebAppAuth(bot_token)