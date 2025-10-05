from django.urls import path
from . import views

app_name = 'startup_game'

urlpatterns = [
    path('', views.game_play, name='game'),  # Основная игровая страница /game/
    path('home/', views.game_home, name='home'),
    path('play/', views.game_play, name='play'),  # Для совместимости
    path('company-name/', views.company_name, name='company_name'),
    path('industry-select/', views.industry_select, name='industry_select'),
    path('new-game/', views.new_game, name='new_game'),
    path('stats/', views.game_stats, name='stats'),
    path('api/action/', views.game_action, name='game_action'),
    path('api/sync-time/', views.sync_time, name='sync_time'),
    path('api/choice/', views.process_choice, name='process_choice'),
]