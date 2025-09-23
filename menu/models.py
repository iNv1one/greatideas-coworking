from django.db import models
from cafes.models import Cafe


class Category(models.Model):
    """Категории меню для каждого кафе"""
    
    cafe = models.ForeignKey(Cafe, on_delete=models.CASCADE, verbose_name="Кафе")
    name = models.CharField(max_length=100, verbose_name="Название категории")
    description = models.TextField(blank=True, verbose_name="Описание")
    image = models.ImageField(upload_to='categories/', blank=True, verbose_name="Изображение")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['cafe', 'order', 'name']
        unique_together = ['cafe', 'name']
    
    def __str__(self):
        return f"{self.cafe.name} - {self.name}"


class MenuItem(models.Model):
    """Позиции меню"""
    
    cafe = models.ForeignKey(Cafe, on_delete=models.CASCADE, verbose_name="Кафе")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    
    name = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    
    # Изображения
    image = models.ImageField(upload_to='menu_items/', blank=True, verbose_name="Изображение")
    
    # Характеристики
    weight = models.CharField(max_length=50, blank=True, verbose_name="Вес/объем")
    calories = models.PositiveIntegerField(null=True, blank=True, verbose_name="Калории")
    
    # Настройки
    is_active = models.BooleanField(default=True, verbose_name="Доступно")
    is_popular = models.BooleanField(default=False, verbose_name="Популярное")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Позиция меню"
        verbose_name_plural = "Позиции меню"
        ordering = ['cafe', 'category', 'order', 'name']
    
    def __str__(self):
        return f"{self.cafe.name} - {self.name}"

    def get_base_price(self):
        """Базовая цена (для совместимости)"""
        return self.price

    def get_variants(self):
        """Получить все варианты размеров"""
        return self.variants.filter(is_active=True).order_by('order', 'name')

    def has_variants(self):
        """Проверить, есть ли варианты размеров"""
        return self.variants.filter(is_active=True).exists()


class MenuItemVariant(models.Model):
    """Варианты размеров для позиций меню (например, разные объемы напитков)"""
    
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='variants', verbose_name="Позиция меню")
    
    name = models.CharField(max_length=100, verbose_name="Название варианта")  # например "Маленький", "Большой"
    size = models.CharField(max_length=50, verbose_name="Размер")  # например "250 мл", "400 мл"
    price_modifier = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Изменение цены")  # +50 руб к базовой цене
    
    is_default = models.BooleanField(default=False, verbose_name="По умолчанию")
    is_active = models.BooleanField(default=True, verbose_name="Доступен")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Вариант размера"
        verbose_name_plural = "Варианты размеров"
        ordering = ['menu_item', 'order', 'name']
        unique_together = ['menu_item', 'name']
    
    def __str__(self):
        return f"{self.menu_item.name} - {self.name} ({self.size})"
    
    def get_price(self):
        """Получить цену с учетом модификатора"""
        return self.menu_item.price + self.price_modifier


class Addon(models.Model):
    """Добавки для позиций меню"""
    
    ADDON_TYPES = [
        ('milk', 'Молоко'),
        ('syrup', 'Сироп'),
        ('spice', 'Специи'),
        ('extra', 'Дополнительно'),
        ('other', 'Другое'),
    ]
    
    cafe = models.ForeignKey(Cafe, on_delete=models.CASCADE, verbose_name="Кафе")
    group = models.ForeignKey('AddonGroup', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Группа")
    menu_items = models.ManyToManyField(MenuItem, blank=True, verbose_name="Применимо к позициям")
    categories = models.ManyToManyField(Category, blank=True, verbose_name="Применимо к категориям")
    
    name = models.CharField(max_length=100, verbose_name="Название добавки")
    addon_type = models.CharField(max_length=20, choices=ADDON_TYPES, default='other', verbose_name="Тип добавки")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    
    is_active = models.BooleanField(default=True, verbose_name="Доступна")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Добавка"
        verbose_name_plural = "Добавки"
        ordering = ['cafe', 'group', 'addon_type', 'order', 'name']
        unique_together = ['cafe', 'name']
    
    def __str__(self):
        return f"{self.cafe.name} - {self.name} (+{self.price}₽)"
    
    def is_applicable_to_item(self, menu_item):
        """Проверить, применима ли добавка к данной позиции"""
        # Если добавка привязана к конкретным позициям
        if self.menu_items.exists():
            return self.menu_items.filter(id=menu_item.id).exists()
        
        # Если добавка привязана к категориям
        if self.categories.exists():
            return self.categories.filter(id=menu_item.category.id).exists()
        
        # Если не привязана ни к чему, то применима ко всем
        return True


class AddonGroup(models.Model):
    """Группы добавок (например, 'Тип молока', 'Сиропы')"""
    
    cafe = models.ForeignKey(Cafe, on_delete=models.CASCADE, verbose_name="Кафе")
    name = models.CharField(max_length=100, verbose_name="Название группы")
    is_required = models.BooleanField(default=False, verbose_name="Обязательная группа")
    max_selections = models.PositiveIntegerField(default=1, verbose_name="Максимум выборов")
    
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Группа добавок"
        verbose_name_plural = "Группы добавок"
        ordering = ['cafe', 'order', 'name']
        unique_together = ['cafe', 'name']
    
    def __str__(self):
        return f"{self.cafe.name} - {self.name}"
