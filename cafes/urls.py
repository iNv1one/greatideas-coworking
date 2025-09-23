from django.urls import path
from . import views

app_name = 'cafes'

urlpatterns = [
    path('', views.home, name='home'),
    path('cafes/', views.cafe_list, name='list'),
    path('cafe/<int:cafe_id>/', views.cafe_detail, name='detail'),
    path('cart/', views.cart, name='cart'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('update-cart-item/', views.update_cart_item, name='update_cart_item'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
]