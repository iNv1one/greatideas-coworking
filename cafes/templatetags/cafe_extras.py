from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Получить элемент из словаря по ключу
    Используется в шаблонах как: {{ dict|get_item:key }}
    """
    return dictionary.get(key, [])

@register.filter
def keyvalue(dict, key):
    """
    Альтернативный фильтр для получения значения из словаря
    """
    return dict.get(key, [])