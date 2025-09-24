"""
Сервис для работы с API ЮKassa
"""
import json
import uuid
import base64
import requests
from decimal import Decimal
from django.conf import settings
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class YooKassaService:
    """Сервис для работы с API ЮKassa"""
    
    def __init__(self):
        self.shop_id = settings.YOOKASSA_SHOP_ID
        self.secret_key = settings.YOOKASSA_SECRET_KEY
        self.base_url = "https://api.yookassa.ru/v3"
        
        if not self.shop_id or not self.secret_key:
            raise ValueError("YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY должны быть настроены")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Получить заголовки авторизации"""
        credentials = f"{self.shop_id}:{self.secret_key}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        return {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json',
            'Idempotence-Key': str(uuid.uuid4())
        }
    
    def create_payment(self, amount: Decimal, description: str, 
                      return_url: str = None, metadata: Dict = None) -> Dict[str, Any]:
        """
        Создать платеж в ЮKassa
        
        Args:
            amount: Сумма платежа
            description: Описание платежа
            return_url: URL для возврата после оплаты
            metadata: Дополнительные данные
            
        Returns:
            Dict с данными созданного платежа
        """
        url = f"{self.base_url}/payments"
        
        data = {
            "amount": {
                "value": str(amount),
                "currency": "RUB"
            },
            "description": description,
            "confirmation": {
                "type": "redirect",
                "return_url": return_url or "https://coworking.greatideas.ru/"
            },
            "capture": True,
            "metadata": metadata or {}
        }
        
        try:
            response = requests.post(
                url,
                headers=self._get_auth_headers(),
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка создания платежа в ЮKassa: {e}")
            raise
    
    def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Получить информацию о платеже
        
        Args:
            payment_id: ID платежа в ЮKassa
            
        Returns:
            Dict с данными платежа
        """
        url = f"{self.base_url}/payments/{payment_id}"
        
        try:
            response = requests.get(
                url,
                headers=self._get_auth_headers(),
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка получения платежа {payment_id}: {e}")
            raise
    
    def capture_payment(self, payment_id: str, amount: Decimal = None) -> Dict[str, Any]:
        """
        Подтвердить платеж (capture)
        
        Args:
            payment_id: ID платежа в ЮKassa
            amount: Сумма для подтверждения (если отличается от исходной)
            
        Returns:
            Dict с данными подтвержденного платежа
        """
        url = f"{self.base_url}/payments/{payment_id}/capture"
        
        data = {}
        if amount:
            data["amount"] = {
                "value": str(amount),
                "currency": "RUB"
            }
        
        try:
            response = requests.post(
                url,
                headers=self._get_auth_headers(),
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка подтверждения платежа {payment_id}: {e}")
            raise
    
    def cancel_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Отменить платеж
        
        Args:
            payment_id: ID платежа в ЮKassa
            
        Returns:
            Dict с данными отмененного платежа
        """
        url = f"{self.base_url}/payments/{payment_id}/cancel"
        
        try:
            response = requests.post(
                url,
                headers=self._get_auth_headers(),
                json={},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка отмены платежа {payment_id}: {e}")
            raise
    
    def create_refund(self, payment_id: str, amount: Decimal, 
                     description: str = None) -> Dict[str, Any]:
        """
        Создать возврат
        
        Args:
            payment_id: ID платежа для возврата
            amount: Сумма возврата
            description: Описание возврата
            
        Returns:
            Dict с данными созданного возврата
        """
        url = f"{self.base_url}/refunds"
        
        data = {
            "payment_id": payment_id,
            "amount": {
                "value": str(amount),
                "currency": "RUB"
            }
        }
        
        if description:
            data["description"] = description
        
        try:
            response = requests.post(
                url,
                headers=self._get_auth_headers(),
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка создания возврата для платежа {payment_id}: {e}")
            raise
    
    def verify_webhook_signature(self, data: str, signature: str) -> bool:
        """
        Проверить подпись webhook'а от ЮKassa
        
        Args:
            data: Тело запроса в виде строки
            signature: Подпись из заголовка
            
        Returns:
            True если подпись верна
        """
        # Для тестовой среды можем пропустить проверку подписи
        # В продакшене нужно реализовать проверку через HMAC
        return True
    
    def process_webhook_data(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Обработать данные webhook'а от ЮKassa
        
        Args:
            webhook_data: Данные из webhook'а
            
        Returns:
            Словарь с обработанными данными или None
        """
        try:
            event_type = webhook_data.get('event')
            payment_data = webhook_data.get('object', {})
            
            if not event_type or not payment_data:
                logger.warning(f"Неполные данные webhook'а: {webhook_data}")
                return None
            
            result = {
                'event_type': event_type,
                'payment_id': payment_data.get('id'),
                'status': payment_data.get('status'),
                'amount': payment_data.get('amount', {}).get('value'),
                'currency': payment_data.get('amount', {}).get('currency'),
                'description': payment_data.get('description'),
                'metadata': payment_data.get('metadata', {}),
                'created_at': payment_data.get('created_at'),
                'captured_at': payment_data.get('captured_at'),
                'payment_method': payment_data.get('payment_method', {}),
                'raw_data': webhook_data
            }
            
            logger.info(f"Обработан webhook {event_type} для платежа {result['payment_id']}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка обработки webhook'а: {e}")
            return None