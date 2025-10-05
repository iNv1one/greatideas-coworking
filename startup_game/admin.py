from django.contrib import admin
from .models import GameSession, GameEvent, Achievement, UserAchievement


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'company_name', 'day', 'money', 'reputation', 'employees', 'customers', 'is_active', 'updated_at']
    list_filter = ['is_active', 'game_over', 'victory', 'level']
    search_fields = ['user__username', 'company_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(GameEvent)
class GameEventAdmin(admin.ModelAdmin):
    list_display = ['session', 'event_type', 'title', 'day_occurred', 'money_change', 'reputation_change']
    list_filter = ['event_type', 'day_occurred']
    search_fields = ['title', 'description', 'session__company_name']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'icon']
    search_fields = ['name', 'description']


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement', 'session', 'earned_at']
    list_filter = ['earned_at', 'achievement']
    search_fields = ['user__username', 'achievement__name']