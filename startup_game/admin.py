from django.contrib import admin
from .models import GameSession, GameEvent, Achievement, UserAchievement, EventTemplate, EventChoice, Skill, CompletedEvent


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
        'time_cost', 'money_cost', 'button_style', 'skills',
        'money_effect', 'reputation_effect', 'employees_effect', 'customers_effect',
        'prototype_skill_effect', 'presentation_skill_effect', 'pitching_skill_effect', 'team_skill_effect', 'marketing_skill_effect'
    ]
    filter_horizontal = ['skills']


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
            'fields': ('prototype_skill_effect', 'presentation_skill_effect', 'pitching_skill_effect', 'team_skill_effect', 'marketing_skill_effect')
        }),
        ('Связанные навыки', {
            'fields': ('skills',)
        }),
        ('Внешний вид', {
            'fields': ('button_style',)
        }),
    )
    filter_horizontal = ['skills']


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'color', 'is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name', 'display_name', 'description']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'display_name', 'description')
        }),
        ('Настройки игры', {
            'fields': ('session_field', 'is_active', 'order')
        }),
        ('Внешний вид', {
            'fields': ('color', 'icon')
        }),
    )


@admin.register(CompletedEvent)
class CompletedEventAdmin(admin.ModelAdmin):
    list_display = ['session', 'event_key', 'choice_id', 'game_day', 'completed_at']
    list_filter = ['completed_at', 'game_day', 'event_template']
    search_fields = ['session__company_name', 'session__user__username', 'event_key', 'choice_id']
    readonly_fields = ['completed_at']
    raw_id_fields = ['session', 'event_template']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session__user', 'event_template')