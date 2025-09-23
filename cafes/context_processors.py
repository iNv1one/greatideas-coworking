def cart_context(request):
    """Контекстный процессор для корзины"""
    cart = request.session.get('cart', {})
    total_items = 0
    
    for cart_data in cart.values():
        if isinstance(cart_data, int):
            total_items += cart_data
        else:
            total_items += cart_data.get('quantity', 0)
    
    return {
        'cart_total_items': total_items,  # Общее количество товаров в навбаре
    }