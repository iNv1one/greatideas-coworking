"""
Утилиты для работы с Telegram Payments
"""
import uuid
from decimal import Decimal
from telegram import LabeledPrice
from django.conf import settings
from orders.models import Order, OrderItem
from payments.models import Payment
from users.models import TelegramUser


class TelegramPaymentService:
    """Сервис для работы с платежами через Telegram"""
    
    def __init__(self):
        self.provider_token = settings.PAYMENT_PROVIDER_TOKEN
        if not self.provider_token:
            raise ValueError("PAYMENT_PROVIDER_TOKEN не настроен")
    
    def create_order_from_cart(self, telegram_user: TelegramUser, cart_data: dict, 
                              delivery_type: str = 'pickup', 
                              customer_name: str = '', 
                              customer_phone: str = '',
                              delivery_address: str = '',
                              comment: str = '') -> Order:
        """
        Создает заказ из данных корзины
        
        Args:
            telegram_user: Пользователь Telegram
            cart_data: Данные корзины из сессии
            delivery_type: Тип доставки ('pickup' или 'delivery')
            customer_name: Имя клиента
            customer_phone: Телефон клиента
            delivery_address: Адрес доставки
            comment: Комментарий к заказу
            
        Returns:
            Order: Созданный заказ
        """
        from cafes.models import Cafe
        from menu.models import MenuItem, MenuItemVariant, Addon
        
        # Определяем кафе (берем из первого товара)
        print(f"DEBUG: cart_data = {cart_data}")
        
        # Проверяем формат данных корзины
        if not cart_data:
            raise ValueError("Корзина пуста")
        
        first_item_data = next(iter(cart_data.values()))
        print(f"DEBUG: first_item_data = {first_item_data}")
        
        # Определяем item_id в зависимости от формата данных
        if isinstance(first_item_data, int):
            # Старый формат: {item_id: quantity}
            first_item_id = next(iter(cart_data.keys()))
        elif isinstance(first_item_data, dict) and 'item_id' in first_item_data:
            # Формат: {key: {item_id: ..., quantity: ...}}
            first_item_id = first_item_data['item_id']
        elif isinstance(first_item_data, dict) and 'quantity' in first_item_data:
            # Формат: {item_id: {quantity: ...}} - item_id в ключе
            first_cart_key = next(iter(cart_data.keys()))
            print(f"DEBUG: Используем item_id из ключа: {first_cart_key}")
            
            # Парсим формат "1_v1" или просто "1"
            if '_v' in str(first_cart_key):
                # Формат "item_id_variant_id"
                first_item_id = str(first_cart_key).split('_v')[0]
                print(f"DEBUG: Извлечен item_id из '{first_cart_key}': {first_item_id}")
            else:
                first_item_id = first_cart_key
        else:
            print(f"ERROR: Неизвестный формат данных корзины: {type(first_item_data)}, {first_item_data}")
            raise ValueError(f"Неизвестный формат данных корзины: {first_item_data}")
        
        first_item = MenuItem.objects.get(id=first_item_id)
        cafe = first_item.cafe
        
        # Генерируем номер заказа
        order_number = self._generate_order_number()
        
        # Подсчитываем общую сумму
        total_amount = Decimal('0')
        order_items = []
        
        for cart_key, cart_item_data in cart_data.items():
            try:
                # Получаем данные товара
                if isinstance(cart_item_data, int):
                    # Старый формат корзины: {item_id: quantity}
                    item_id = cart_key
                    quantity = cart_item_data
                    variant_id = None
                    addon_ids = []
                elif isinstance(cart_item_data, dict) and 'item_id' in cart_item_data:
                    # Формат: {key: {item_id: ..., quantity: ...}}
                    item_id = cart_item_data['item_id']
                    quantity = cart_item_data['quantity']
                    variant_id = cart_item_data.get('variant_id')
                    addon_ids = cart_item_data.get('addon_ids', [])
                elif isinstance(cart_item_data, dict) and 'quantity' in cart_item_data:
                    # Формат: {item_id: {quantity: ...}} - item_id в ключе
                    # Парсим формат "1_v1" или просто "1"
                    if '_v' in str(cart_key):
                        # Формат "item_id_variant_id"
                        parts = str(cart_key).split('_v')
                        item_id = parts[0]
                        variant_id = parts[1] if len(parts) > 1 else None
                        print(f"DEBUG: Парсинг {cart_key}: item_id={item_id}, variant_id={variant_id}")
                    else:
                        item_id = cart_key
                        variant_id = cart_item_data.get('variant_id')
                    
                    quantity = cart_item_data['quantity']
                    addon_ids = cart_item_data.get('addon_ids', [])
                    print(f"DEBUG: Обрабатываем товар {item_id} с количеством {quantity}")
                else:
                    print(f"ERROR: Неизвестный формат элемента корзины: {cart_key} = {cart_item_data}")
                    continue
                
                menu_item = MenuItem.objects.get(id=item_id)
                
                # Базовая цена
                unit_price = menu_item.price
                
                # Цена варианта
                variant = None
                if variant_id:
                    try:
                        variant = MenuItemVariant.objects.get(id=variant_id)
                        unit_price += variant.price_modifier
                    except MenuItemVariant.DoesNotExist:
                        pass
                
                # Цена добавок
                selected_addons = []
                if addon_ids:
                    addons = Addon.objects.filter(id__in=addon_ids)
                    selected_addons = list(addons)
                    unit_price += sum(addon.price for addon in addons)
                
                # Общая цена за позицию
                item_total = unit_price * quantity
                total_amount += item_total
                
                order_items.append({
                    'menu_item': menu_item,
                    'variant': variant,
                    'addons': selected_addons,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': item_total,
                })
                
            except MenuItem.DoesNotExist:
                continue
        
        # Создаем заказ
        order = Order.objects.create(
            cafe=cafe,
            user=telegram_user,
            order_number=order_number,
            status='pending',
            delivery_type=delivery_type,
            total_amount=total_amount,
            delivery_fee=Decimal('0'),  # Пока без доставки
            customer_name=customer_name or telegram_user.full_name,
            customer_phone=customer_phone,
            delivery_address=delivery_address,
            comment=comment,
        )
        
        # Создаем позиции заказа
        for item_data in order_items:
            order_item = OrderItem.objects.create(
                order=order,
                menu_item=item_data['menu_item'],
                variant=item_data['variant'],
                quantity=item_data['quantity'],
                base_price=item_data['menu_item'].price,
                final_price=item_data['unit_price'],
                total_price=item_data['total_price'],
            )
            
            # Добавляем добавки через промежуточную модель
            for addon in item_data['addons']:
                from orders.models import OrderItemAddon
                OrderItemAddon.objects.create(
                    order_item=order_item,
                    addon=addon
                )
        
        return order
    
    def create_payment(self, order: Order) -> Payment:
        """Создает запись о платеже"""
        payment = Payment.objects.create(
            order=order,
            amount=order.total_amount + order.delivery_fee,
            currency='RUB',
            status='pending',
            invoice_payload=f"order_{order.id}_{uuid.uuid4().hex[:8]}",
        )
        return payment
    
    def create_invoice_prices(self, order: Order) -> list[LabeledPrice]:
        """Создает список цен для инвойса Telegram"""
        prices = []
        
        # Добавляем позиции заказа
        for order_item in order.items.all():
            # Основная позиция
            name = order_item.menu_item.name
            if order_item.variant:
                name += f" ({order_item.variant.name})"
            
            price_kopecks = int(order_item.final_price * 100)  # Переводим в копейки
            
            prices.append(LabeledPrice(
                label=f"{name} x{order_item.quantity}",
                amount=price_kopecks * order_item.quantity
            ))
            
            # Добавляем добавки отдельно для наглядности
            for addon in order_item.addons.all():
                prices.append(LabeledPrice(
                    label=f"  + {addon.name}",
                    amount=int(addon.price * 100 * order_item.quantity)
                ))
        
        # Добавляем доставку если есть
        if order.delivery_fee > 0:
            prices.append(LabeledPrice(
                label="Доставка",
                amount=int(order.delivery_fee * 100)
            ))
        
        return prices
    
    def _generate_order_number(self) -> str:
        """Генерирует уникальный номер заказа"""
        import time
        timestamp = str(int(time.time()))[-6:]  # Последние 6 цифр timestamp
        random_part = uuid.uuid4().hex[:4].upper()
        return f"GI{timestamp}{random_part}"
    
    def get_order_by_payment_payload(self, payload: str) -> Order:
        """Получает заказ по payload платежа"""
        try:
            payment = Payment.objects.get(invoice_payload=payload)
            return payment.order
        except Payment.DoesNotExist:
            # Пробуем извлечь ID заказа из payload
            if payload.startswith('order_'):
                order_id = payload.split('_')[1]
                return Order.objects.get(id=order_id)
            raise
    
    def process_successful_payment(self, payment_data: dict) -> Order:
        """Обрабатывает успешный платеж"""
        payload = payment_data.get('invoice_payload')
        telegram_charge_id = payment_data.get('telegram_payment_charge_id')
        provider_charge_id = payment_data.get('provider_payment_charge_id')
        
        order = self.get_order_by_payment_payload(payload)
        
        # Находим или создаем платеж
        try:
            payment = Payment.objects.get(order=order)
        except Payment.DoesNotExist:
            payment = self.create_payment(order)
        
        # Отмечаем как оплаченный
        payment.mark_as_paid(telegram_charge_id, provider_charge_id)
        
        return order