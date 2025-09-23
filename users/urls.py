from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('telegram-login/', views.telegram_login_view, name='telegram_login'),
    path('telegram-auth/', views.telegram_auth_callback, name='telegram_auth'),
]