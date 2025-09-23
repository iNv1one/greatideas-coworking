from django.contrib import admin
from .models import Cafe


@admin.register(Cafe)
class CafeAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'address', 'phone']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'description', 'address', 'phone', 'working_hours')
        }),
        ('Изображения', {
            'fields': ('logo', 'cover_image')
        }),
        ('Настройки', {
            'fields': ('is_active', 'min_order_amount', 'delivery_fee')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
