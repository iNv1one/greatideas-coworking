from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'amount', 'method', 'status', 'created_at', 'paid_at']
    list_filter = ['method', 'status', 'currency', 'created_at']
    search_fields = ['order__order_number', 'external_payment_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Заказ', {
            'fields': ('order',)
        }),
        ('Платеж', {
            'fields': ('amount', 'currency', 'method', 'status')
        }),
        ('Внешние идентификаторы', {
            'fields': ('external_payment_id', 'provider_payment_charge_id')
        }),
        ('Дополнительно', {
            'fields': ('description',)
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at', 'paid_at'),
            'classes': ('collapse',)
        }),
    )
