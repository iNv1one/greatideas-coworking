"""
Утилиты для работы с Telegram Payments (исправленная версия)
"""
import uuid
from decimal import Decimal
from telegram import LabeledPrice
from django.conf import settings
from orders.models import Order, OrderItem, OrderItemAddon
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
            cart_data: Данные корзины из сессии (формат: {"1_v2": {"quantity": 1}, "3": {"quantity": 2}})
            delivery_type: Тип доставки ('pickup' или 'delivery')
            customer_name: Имя клиента
            customer_phone: Телефон клиента
            delivery_address: Адрес доставки
            comment: Комментарий к заказу
            
        Returns:
            Order: Созданный заказ
        """
        from menu.models import MenuItem, MenuItemVariant, Addon
        
        print(f"DEBUG: Создание заказа для пользователя {telegram_user.telegram_id}")
        print(f"DEBUG: cart_data = {cart_data}")
        
        # Проверяем, что корзина не пуста
        if not cart_data:
            raise ValueError("Корзина пуста")
        
        # Определяем кафе из первого товара
        first_cart_key = next(iter(cart_data.keys()))
        
        # Парсим item_id из ключа (формат может быть "1" или "1_v2")
        if '_v' in str(first_cart_key):
            first_item_id = str(first_cart_key).split('_v')[0]
        else:
            first_item_id = first_cart_key
        
        try:
            first_item = MenuItem.objects.get(id=int(first_item_id))
            cafe = first_item.cafe
            print(f"DEBUG: Определено кафе: {cafe.name}")
        except (MenuItem.DoesNotExist, ValueError) as e:
            raise ValueError(f"Не удалось найти товар с ID {first_item_id}: {e}")
        
        # Создаем заказ сначала без позиций
        order = Order(
            cafe=cafe,
            user=telegram_user,
            delivery_type=delivery_type,
            customer_name=customer_name or telegram_user.first_name or 'Клиент',
            customer_phone=customer_phone,
            delivery_address=delivery_address,
            comment=comment,
            total_amount=Decimal('0')  # Пока ставим 0, потом пересчитаем
        )
        # order_number будет сгенерирован автоматически в save()
        order.save()
        
        print(f"DEBUG: Создан заказ #{order.order_number}")
        
        total_amount = Decimal('0')
        
        # Обрабатываем каждую позицию корзины
        for cart_key, cart_item_data in cart_data.items():
            try:
                print(f"DEBUG: Обработка позиции {cart_key}: {cart_item_data}")
                
                # Парсим cart_key для извлечения item_id и variant_id
                if '_v' in str(cart_key):
                    parts = str(cart_key).split('_v')
                    item_id = int(parts[0])
                    variant_id = int(parts[1]) if len(parts) > 1 and parts[1] else None
                else:
                    item_id = int(cart_key)
                    variant_id = None
                
                # Получаем количество
                if isinstance(cart_item_data, int):
                    quantity = cart_item_data
                    addon_ids = []
                elif isinstance(cart_item_data, dict):
                    quantity = cart_item_data.get('quantity', 1)
                    addon_ids = cart_item_data.get('addon_ids', [])
                else:
                    print(f"WARNING: Неизвестный формат данных для {cart_key}: {cart_item_data}")
                    continue
                
                # Получаем объекты из базы
                menu_item = MenuItem.objects.get(id=item_id)
                
                variant = None
                if variant_id:
                    try:
                        variant = MenuItemVariant.objects.get(id=variant_id, menu_item=menu_item)
                    except MenuItemVariant.DoesNotExist:
                        print(f"WARNING: Вариант {variant_id} не найден для товара {item_id}")
                
                # Создаем OrderItem - БEЗ автоматических расчетов, делаем вручную
                order_item = OrderItem(
                    order=order,
                    menu_item=menu_item,
                    variant=variant,
                    quantity=quantity,
                    base_price=menu_item.price
                )
                
                # Рассчитываем цены вручную
                variant_price = variant.price_modifier if variant else Decimal('0')
                order_item.variant_price = variant_price
                
                # Сначала сохраняем без добавок
                order_item.addons_price = Decimal('0')
                order_item.final_price = order_item.base_price + variant_price
                order_item.total_price = order_item.final_price * quantity
                order_item.save()
                
                print(f"DEBUG: Создана позиция заказа: {order_item} за {order_item.total_price}")
                
                # Добавляем добавки
                addons_price = Decimal('0')
                if addon_ids:
                    addons = Addon.objects.filter(id__in=addon_ids, cafe=cafe)
                    for addon in addons:
                        OrderItemAddon.objects.create(
                            order_item=order_item,
                            addon=addon
                        )
                        addons_price += addon.price
                        print(f"DEBUG: Добавлена добавка: {addon.name} (+{addon.price})")
                    
                    # Пересчитываем цены с учетом добавок
                    order_item.addons_price = addons_price
                    order_item.final_price = order_item.base_price + variant_price + addons_price
                    order_item.total_price = order_item.final_price * quantity
                    order_item.save()
                
                total_amount += order_item.total_price
                
            except MenuItem.DoesNotExist:
                print(f"ERROR: Товар с ID {item_id} не найден")
                continue
            except Exception as e:
                print(f"ERROR: Ошибка обработки позиции {cart_key}: {e}")
                continue
        
        # Обновляем общую сумму заказа
        order.total_amount = total_amount
        order.save()
        
        print(f"DEBUG: Заказ {order.order_number} создан на сумму {total_amount}")
        
        if order.items.count() == 0:
            order.delete()
            raise ValueError("Не удалось создать ни одной позиции заказа")
        
        return order
    
    def create_payment(self, order: Order) -> Payment:
        """Создает запись о платеже"""
        # Проверяем, есть ли уже платеж для этого заказа
        existing_payment = Payment.objects.filter(order=order).first()
        if existing_payment:
            print(f"DEBUG: Найден существующий платеж для заказа {order.order_number}")
            return existing_payment
        
        # Создаем уникальный invoice_payload на основе номера заказа
        invoice_payload = f"order_{order.order_number}_{uuid.uuid4().hex[:8]}"
        
        payment = Payment.objects.create(
            order=order,
            amount=order.total_amount,
            method='telegram',
            status='pending',
            currency='RUB',
            description=f"Оплата заказа #{order.order_number}",
            invoice_payload=invoice_payload,
        )
        print(f"DEBUG: Создан новый платеж для заказа {order.order_number} с payload {invoice_payload}")
        return payment
    
    def create_invoice_prices(self, order: Order) -> list:
        """Создает список цен для Telegram инвойса"""
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
            
            # Добавляем добавки отдельными строками
            for addon_item in order_item.selected_addons.all():
                addon_price_kopecks = int(addon_item.addon.price * 100)
                prices.append(LabeledPrice(
                    label=f"  + {addon_item.addon.name}",
                    amount=addon_price_kopecks * order_item.quantity
                ))
        
        return prices
    
    def get_order_by_payment_payload(self, invoice_payload: str) -> Order:
        """Получает заказ по invoice_payload"""
        try:
            payment = Payment.objects.get(invoice_payload=invoice_payload)
            return payment.order
        except Payment.DoesNotExist:
            raise ValueError(f"Платеж с payload {invoice_payload} не найден")
    
    def process_successful_payment(self, payment_data: dict) -> Order:
        """Обрабатывает успешный платеж"""
        invoice_payload = payment_data['invoice_payload']
        telegram_charge_id = payment_data.get('telegram_payment_charge_id')
        provider_charge_id = payment_data.get('provider_payment_charge_id')
        
        try:
            payment = Payment.objects.get(invoice_payload=invoice_payload)
            payment.mark_as_paid(
                telegram_charge_id=telegram_charge_id,
                provider_charge_id=provider_charge_id
            )
            return payment.order
        except Payment.DoesNotExist:
            raise ValueError(f"Платеж с payload {invoice_payload} не найден")
    
    def _generate_order_number(self) -> str:
        """Генерирует номер заказа"""
        from django.utils import timezone
        
        today = timezone.now().strftime('%Y%m%d')
        last_order = Order.objects.filter(
            created_at__date=timezone.now().date()
        ).order_by('-id').first()
        
        if last_order and last_order.order_number.startswith(today):
            sequence = int(last_order.order_number[-3:]) + 1
        else:
            sequence = 1
        
        return f"{today}{sequence:03d}"