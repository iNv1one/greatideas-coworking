from django.contrib import admin
from .models import Order, OrderItem, OrderItemAddon


class OrderItemAddonInline(admin.TabularInline):
    """Inline для добавок к позиции заказа"""
    model = OrderItemAddon
    extra = 0


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['base_price', 'variant_price', 'addons_price', 'final_price', 'total_price']
    fields = ['menu_item', 'variant', 'quantity', 'base_price', 'variant_price', 'addons_price', 'final_price', 'total_price', 'comment']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'cafe', 'customer_name', 'status', 'total_amount', 'created_at']
    list_filter = ['cafe', 'status', 'delivery_type', 'created_at']
    search_fields = ['order_number', 'customer_name', 'customer_phone']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('order_number', 'cafe', 'user', 'status', 'delivery_type')
        }),
        ('Клиент', {
            'fields': ('customer_name', 'customer_phone', 'delivery_address')
        }),
        ('Сумма', {
            'fields': ('total_amount', 'delivery_fee')
        }),
        ('Дополнительно', {
            'fields': ('comment',)
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    inlines = [OrderItemAddonInline]
    
    list_display = ['order', 'get_display_name', 'variant', 'quantity', 'final_price', 'total_price']
    list_filter = ['order__cafe', 'menu_item__category']
    readonly_fields = ['base_price', 'variant_price', 'addons_price', 'final_price', 'total_price']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('order', 'menu_item', 'variant', 'quantity')
        }),
        ('Ценообразование', {
            'fields': ('base_price', 'variant_price', 'addons_price', 'final_price', 'total_price'),
            'classes': ('collapse',)
        }),
        ('Дополнительно', {
            'fields': ('comment',)
        }),
    )


@admin.register(OrderItemAddon)
class OrderItemAddonAdmin(admin.ModelAdmin):
    list_display = ['order_item', 'addon', 'get_addon_price']
    list_filter = ['addon__cafe', 'addon__addon_type']
    
    def get_addon_price(self, obj):
        return f"{obj.addon.price} ₽"
    get_addon_price.short_description = "Цена добавки"
