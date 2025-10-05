from django.urls import path
from . import views

app_name = 'startup_game'

urlpatterns = [
    path('', views.game_home, name='home'),
    path('play/', views.game_play, name='play'),
    path('new-game/', views.new_game, name='new_game'),
    path('stats/', views.game_stats, name='stats'),
    path('api/action/', views.game_action, name='game_action'),
]