from django.contrib import admin
from .models import Category, MenuItem, MenuItemVariant, Addon, AddonGroup


class MenuItemVariantInline(admin.TabularInline):
    """Inline для вариантов размеров"""
    model = MenuItemVariant
    extra = 1
    fields = ['name', 'size', 'price_modifier', 'is_default', 'is_active', 'order']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'cafe', 'order', 'is_active']
    list_filter = ['cafe', 'is_active']
    search_fields = ['name', 'cafe__name']
    list_editable = ['order', 'is_active']


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    inlines = [MenuItemVariantInline]
    
    list_display = ['name', 'cafe', 'category', 'price', 'has_variants_display', 'is_active', 'is_popular']
    list_filter = ['cafe', 'category', 'is_active', 'is_popular']
    search_fields = ['name', 'description', 'cafe__name']
    list_editable = ['price', 'is_active', 'is_popular']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('cafe', 'category', 'name', 'description', 'price')
        }),
        ('Изображение и характеристики', {
            'fields': ('image', 'weight', 'calories')
        }),
        ('Настройки', {
            'fields': ('is_active', 'is_popular', 'order')
        }),
    )
    
    def has_variants_display(self, obj):
        """Отображение наличия вариантов"""
        return "✓" if obj.has_variants() else "✗"
    has_variants_display.short_description = "Есть варианты"


@admin.register(MenuItemVariant)
class MenuItemVariantAdmin(admin.ModelAdmin):
    list_display = ['menu_item', 'name', 'size', 'price_modifier', 'get_final_price', 'is_default', 'is_active']
    list_filter = ['menu_item__cafe', 'is_default', 'is_active']
    search_fields = ['menu_item__name', 'name', 'size']
    list_editable = ['price_modifier', 'is_default', 'is_active']
    
    def get_final_price(self, obj):
        """Отображение итоговой цены"""
        return f"{obj.get_price()} ₽"
    get_final_price.short_description = "Итоговая цена"


@admin.register(AddonGroup)
class AddonGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'cafe', 'is_required', 'max_selections', 'is_active', 'order']
    list_filter = ['cafe', 'is_required', 'is_active']
    search_fields = ['name', 'cafe__name']
    list_editable = ['is_required', 'max_selections', 'is_active', 'order']


@admin.register(Addon)
class AddonAdmin(admin.ModelAdmin):
    list_display = ['name', 'cafe', 'group', 'addon_type', 'price', 'is_active']
    list_filter = ['cafe', 'group', 'addon_type', 'is_active']
    search_fields = ['name', 'cafe__name']
    list_editable = ['price', 'is_active']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('cafe', 'group', 'name', 'addon_type', 'price')
        }),
        ('Применимость', {
            'fields': ('menu_items', 'categories'),
            'description': 'Если не выбрано ничего, добавка будет применима ко всем позициям'
        }),
        ('Настройки', {
            'fields': ('is_active', 'order')
        }),
    )
    
    filter_horizontal = ['menu_items', 'categories']
