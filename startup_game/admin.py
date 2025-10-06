from django.contrib import admin
from .models import GameSession, GameEvent, Achievement, UserAchievement, EventTemplate, EventChoice


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


class EventChoiceInline(admin.TabularInline):
    model = EventChoice
    extra = 1
    fields = [
        'choice_id', 'title', 'description', 'order',
        'time_cost', 'money_cost', 'button_style',
        'money_effect', 'reputation_effect', 'employees_effect', 'customers_effect',
        'prototype_skill_effect', 'presentation_skill_effect', 'pitching_skill_effect', 'team_skill_effect'
    ]


@admin.register(EventTemplate)
class EventTemplateAdmin(admin.ModelAdmin):
    list_display = ['title', 'key', 'is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['title', 'key', 'description']
    inlines = [EventChoiceInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('key', 'title', 'description')
        }),
        ('Настройки', {
            'fields': ('is_active', 'order')
        }),
    )


@admin.register(EventChoice)
class EventChoiceAdmin(admin.ModelAdmin):
    list_display = ['event_template', 'title', 'time_cost', 'money_cost', 'order']
    list_filter = ['event_template', 'time_cost', 'button_style']
    search_fields = ['title', 'description', 'event_template__title']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('event_template', 'choice_id', 'title', 'description', 'order')
        }),
        ('Затраты', {
            'fields': ('time_cost', 'money_cost')
        }),
        ('Эффекты на игру', {
            'fields': ('money_effect', 'reputation_effect', 'employees_effect', 'customers_effect')
        }),
        ('Эффекты на навыки', {
            'fields': ('prototype_skill_effect', 'presentation_skill_effect', 'pitching_skill_effect', 'team_skill_effect')
        }),
        ('Внешний вид', {
            'fields': ('button_style',)
        }),
    )