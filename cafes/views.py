from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Cafe
from menu.models import Category, MenuItem, MenuItemVariant, Addon, AddonGroup, MenuItemVariant, Addon, AddonGroup


def home(request):
    """Главная страница с информацией о GreatIdeas"""
    cafes_count = Cafe.objects.filter(is_active=True).count()
    context = {
        'cafes_count': cafes_count,
    }
    return render(request, 'home.html', context)


def cafe_list(request):
    """Список всех активных кафе или перенаправление на единственное кафе"""
    cafes = Cafe.objects.filter(is_active=True).order_by('name')
    
    # Если кафе только одно, сразу перенаправляем на его страницу
    if cafes.count() == 1:
        return redirect('cafes:detail', cafe_id=cafes.first().id)
    
    # Если кафе несколько, показываем список для выбора
    context = {
        'cafes': cafes,
    }
    return render(request, 'cafes/list.html', context)


def cafe_detail(request, cafe_id):
    """Страница конкретного кафе с меню"""
    cafe = get_object_or_404(Cafe, id=cafe_id, is_active=True)
    categories = Category.objects.filter(cafe=cafe, is_active=True).order_by('order', 'name')
    
    # Получаем меню по категориям
    menu_by_category = {}
    menu_items_json = {}
    
    for category in categories:
        items = MenuItem.objects.filter(
            cafe=cafe, 
            category=category, 
            is_active=True
        ).order_by('order', 'name').prefetch_related('variants')
        
        if items.exists():
            menu_by_category[category] = items
            
            # Формируем JSON данные для JavaScript
            for item in items:
                variants = []
                for variant in item.variants.filter(is_active=True):
                    variants.append({
                        'id': variant.id,
                        'name': variant.name,
                        'size': variant.size,
                        'priceModifier': float(variant.price_modifier),
                        'isDefault': variant.is_default
                    })
                
                # Получаем применимые добавки
                applicable_addons = []
                for addon in Addon.objects.filter(cafe=cafe, is_active=True):
                    if addon.is_applicable_to_item(item):
                        applicable_addons.append({
                            'id': addon.id,
                            'name': addon.name,
                            'price': float(addon.price),
                            'type': addon.addon_type,
                            'group': addon.group.name if addon.group else addon.get_addon_type_display()
                        })
                
                menu_items_json[item.id] = {
                    'id': item.id,
                    'name': item.name,
                    'basePrice': float(item.price),
                    'variants': variants,
                    'addons': applicable_addons
                }
    
    # Находим первое популярное блюдо
    popular_item = MenuItem.objects.filter(
        cafe=cafe, 
        is_active=True, 
        is_popular=True
    ).first()
    
    # Получаем доступные добавки для кафе
    addon_groups = AddonGroup.objects.filter(
        cafe=cafe, 
        is_active=True
    ).order_by('order', 'name').prefetch_related('addon_set')
    
    # Получаем все добавки для кафе
    addons = Addon.objects.filter(
        cafe=cafe, 
        is_active=True
    ).order_by('group', 'order', 'name')
    
    # Подсчитываем количество товаров по категориям
    category_counts = {}
    for category in categories:
        items = MenuItem.objects.filter(
            cafe=cafe, 
            category=category, 
            is_active=True
        )
        category_counts[category.id] = items.count()
    
    import json
    
    # Проверяем количество всех активных кафе
    total_cafes_count = Cafe.objects.filter(is_active=True).count()
    
    context = {
        'cafe': cafe,
        'categories': categories,
        'menu_by_category': menu_by_category,
        'category_counts': category_counts,
        'popular_item': popular_item,
        'addon_groups': addon_groups,
        'addons': addons,
        'total_cafes_count': total_cafes_count,
        'menu_items_json': json.dumps(menu_items_json),
    }
    return render(request, 'cafes/detail.html', context)


def add_to_cart(request):
    """AJAX добавление товара в корзину"""
    if request.method == 'POST':
        import json
        
        # Определяем формат данных
        if request.content_type == 'application/json':
            # Данные в формате JSON
            data = json.loads(request.body)
            item_id = data.get('item_id')
            variant_id = data.get('variant_id')
            quantity = int(data.get('quantity', 1))
            addon_ids = data.get('addon_ids', [])
        else:
            # Данные в формате POST
            item_id = request.POST.get('item_id')
            variant_id = request.POST.get('variant_id')
            quantity = int(request.POST.get('quantity', 1))
            addon_ids = request.POST.getlist('addon_ids[]')
        
        # Создаем уникальный ключ для корзины
        cart_key = f"{item_id}"
        if variant_id:
            cart_key += f"_v{variant_id}"
        if addon_ids:
            addon_ids_sorted = sorted(map(str, addon_ids))
            cart_key += f"_a{'_'.join(addon_ids_sorted)}"
        
        # Получаем корзину из сессии
        cart = request.session.get('cart', {})
        
        if cart_key in cart:
            cart[cart_key]['quantity'] += quantity
        else:
            cart[cart_key] = {
                'item_id': item_id,
                'variant_id': variant_id,
                'addon_ids': addon_ids,
                'quantity': quantity,
            }
            
        request.session['cart'] = cart
        request.session.modified = True
        
        # Подсчитываем общее количество товаров в корзине
        total_items = sum(item['quantity'] for item in cart.values())
        
        return JsonResponse({
            'success': True,
            'total_items': total_items,
            'cart_count': total_items,  # Общее количество товаров для навбара
            'message': 'Товар добавлен в корзину'
        })
    
    return JsonResponse({'success': False})


def cart(request):
    """Страница корзины"""
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    
    for cart_key, cart_data in cart.items():
        try:
            # Для обратной совместимости со старым форматом корзины
            if isinstance(cart_data, int):
                item_id = cart_key
                quantity = cart_data
                variant_id = None
                addon_ids = []
            else:
                item_id = cart_data['item_id']
                quantity = cart_data['quantity']
                variant_id = cart_data.get('variant_id')
                addon_ids = cart_data.get('addon_ids', [])
            
            menu_item = MenuItem.objects.get(id=item_id)
            
            # Базовая цена
            base_price = menu_item.price
            
            # Цена варианта
            variant_price = 0
            variant = None
            if variant_id:
                try:
                    variant = MenuItemVariant.objects.get(id=variant_id)
                    variant_price = variant.price_modifier
                except MenuItemVariant.DoesNotExist:
                    pass
            
            # Цена добавок
            addons_price = 0
            selected_addons = []
            if addon_ids:
                addons = Addon.objects.filter(id__in=addon_ids)
                selected_addons = list(addons)
                addons_price = sum(addon.price for addon in addons)
            
            # Итоговая цена за единицу
            unit_price = base_price + variant_price + addons_price
            item_total = unit_price * quantity
            total_price += item_total
            
            cart_items.append({
                'cart_key': cart_key,
                'item': menu_item,
                'variant': variant,
                'addons': selected_addons,
                'quantity': quantity,
                'base_price': base_price,
                'variant_price': variant_price,
                'addons_price': addons_price,
                'unit_price': unit_price,
                'total_price': item_total,
            })
        except MenuItem.DoesNotExist:
            continue
    
    # Подсчитываем общее количество товаров
    total_items = sum(item['quantity'] for item in cart_items)
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'cart_count': len(cart_items),
        'total_items': total_items,
    }
    return render(request, 'cafes/cart.html', context)


def update_cart_item(request):
    """AJAX обновление количества товара в корзине"""
    if request.method == 'POST':
        import json
        
        data = json.loads(request.body)
        cart_key = data.get('cart_key')
        new_quantity = int(data.get('quantity', 1))
        
        cart = request.session.get('cart', {})
        
        if cart_key in cart and new_quantity > 0:
            cart[cart_key]['quantity'] = new_quantity
            request.session['cart'] = cart
            request.session.modified = True
            
            # Подсчитываем новую общую стоимость
            total_price = 0
            total_items = 0
            
            for cart_data in cart.values():
                try:
                    if isinstance(cart_data, int):
                        item_id = cart_key
                        quantity = cart_data
                        variant_id = None
                        addon_ids = []
                    else:
                        item_id = cart_data['item_id']
                        quantity = cart_data['quantity']
                        variant_id = cart_data.get('variant_id')
                        addon_ids = cart_data.get('addon_ids', [])
                    
                    menu_item = MenuItem.objects.get(id=item_id)
                    unit_price = menu_item.price
                    
                    if variant_id:
                        try:
                            variant = MenuItemVariant.objects.get(id=variant_id)
                            unit_price += variant.price_modifier
                        except MenuItemVariant.DoesNotExist:
                            pass
                    
                    if addon_ids:
                        addons = Addon.objects.filter(id__in=addon_ids)
                        unit_price += sum(addon.price for addon in addons)
                    
                    total_price += unit_price * quantity
                    total_items += quantity
                    
                except MenuItem.DoesNotExist:
                    continue
            
            return JsonResponse({
                'success': True,
                'total_price': total_price,
                'total_items': total_items  # Общее количество товаров для навбара
            })
    
    return JsonResponse({'success': False})


def remove_from_cart(request):
    """AJAX удаление товара из корзины"""
    if request.method == 'POST':
        import json
        
        data = json.loads(request.body)
        cart_key = data.get('cart_key')
        
        cart = request.session.get('cart', {})
        
        if cart_key in cart:
            del cart[cart_key]
            request.session['cart'] = cart
            request.session.modified = True
            
            # Проверяем, пуста ли корзина
            cart_empty = len(cart) == 0
            
            if not cart_empty:
                # Подсчитываем новую общую стоимость
                total_price = 0
                total_items = 0
                
                for cart_data in cart.values():
                    try:
                        if isinstance(cart_data, int):
                            item_id = cart_key
                            quantity = cart_data
                            variant_id = None
                            addon_ids = []
                        else:
                            item_id = cart_data['item_id']
                            quantity = cart_data['quantity']
                            variant_id = cart_data.get('variant_id')
                            addon_ids = cart_data.get('addon_ids', [])
                        
                        menu_item = MenuItem.objects.get(id=item_id)
                        unit_price = menu_item.price
                        
                        if variant_id:
                            try:
                                variant = MenuItemVariant.objects.get(id=variant_id)
                                unit_price += variant.price_modifier
                            except MenuItemVariant.DoesNotExist:
                                pass
                        
                        if addon_ids:
                            addons = Addon.objects.filter(id__in=addon_ids)
                            unit_price += sum(addon.price for addon in addons)
                        
                        total_price += unit_price * quantity
                        total_items += quantity
                        
                    except MenuItem.DoesNotExist:
                        continue
            else:
                total_price = 0
                total_items = 0
            
            return JsonResponse({
                'success': True,
                'cart_empty': cart_empty,
                'total_price': total_price,
                'total_items': total_items  # Общее количество товаров для навбара
            })
    
    return JsonResponse({'success': False})
