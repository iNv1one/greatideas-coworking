from django.db import models
from django.contrib.auth.models import User


class GameSession(models.Model):
    """Игровая сессия пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Игровые параметры
    company_name = models.CharField(max_length=100, default='My Startup')
    money = models.IntegerField(default=1000)  # Деньги
    reputation = models.IntegerField(default=0)  # Репутация
    employees = models.IntegerField(default=1)  # Сотрудники
    customers = models.IntegerField(default=0)  # Клиенты
    day = models.IntegerField(default=1)  # Игровой день
    level = models.IntegerField(default=1)  # Уровень
    
    # Игровое состояние
    is_active = models.BooleanField(default=True)
    game_over = models.BooleanField(default=False)
    victory = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Game Session'
        verbose_name_plural = 'Game Sessions'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.company_name} (Day {self.day})"


class GameEvent(models.Model):
    """События в игре"""
    EVENT_TYPES = (
        ('opportunity', 'Возможность'),
        ('challenge', 'Вызов'),
        ('news', 'Новость'),
        ('decision', 'Решение'),
    )
    
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    day_occurred = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Влияние на параметры
    money_change = models.IntegerField(default=0)
    reputation_change = models.IntegerField(default=0)
    employees_change = models.IntegerField(default=0)
    customers_change = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = 'Game Event'
        verbose_name_plural = 'Game Events'
        ordering = ['-day_occurred']
    
    def __str__(self):
        return f"{self.title} (Day {self.day_occurred})"


class Achievement(models.Model):
    """Достижения"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='fas fa-trophy')  # FontAwesome иконка
    
    # Условия получения
    required_money = models.IntegerField(null=True, blank=True)
    required_reputation = models.IntegerField(null=True, blank=True)
    required_employees = models.IntegerField(null=True, blank=True)
    required_customers = models.IntegerField(null=True, blank=True)
    required_day = models.IntegerField(null=True, blank=True)
    required_level = models.IntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Achievement'
        verbose_name_plural = 'Achievements'
    
    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    """Достижения пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'User Achievement'
        verbose_name_plural = 'User Achievements'
        unique_together = ['user', 'achievement']
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"