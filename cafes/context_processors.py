def cart_context(request):
    """Контекст корзины для всех страниц"""
    cart = {}
    cart_count = 0
    
    # Проверяем, что сессия доступна
    if hasattr(request, 'session') and request.session:
        try:
            cart = request.session.get('cart', {})
            cart_count = sum(item.get('quantity', 0) for item in cart.values())
        except Exception:
            # Если что-то пошло не так с сессией, просто используем пустую корзину
            cart = {}
            cart_count = 0
    
    return {
        'cart_count': cart_count,
        'cart': cart
    }