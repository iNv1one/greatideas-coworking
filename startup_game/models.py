from django.db import models
from django.contrib.auth.models import User


class GameSession(models.Model):
    """Игровая сессия пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Игровые параметры
    company_name = models.CharField(max_length=100, default='My Startup')
    industry = models.CharField(max_length=50, default='IT', choices=[
        ('IT', 'Информационные технологии'),
        ('FOOD', 'Еда и рестораны'),
        ('RETAIL', 'Розничная торговля'),
        ('HEALTH', 'Здравоохранение'),
        ('EDUCATION', 'Образование'),
    ])
    money = models.IntegerField(default=500)  # Деньги
    reputation = models.IntegerField(default=0)  # Репутация
    employees = models.IntegerField(default=1)  # Сотрудники
    customers = models.IntegerField(default=0)  # Клиенты
    day = models.IntegerField(default=1)  # Игровой день
    level = models.IntegerField(default=1)  # Уровень
    
    # Игровое время (в минутах от начала дня, 0-1440)
    game_time = models.IntegerField(default=480)  # Начинаем с 8:00 (480 минут)
    
    # События и решения
    last_event_day = models.IntegerField(default=0)  # Последний день события
    last_decision = models.CharField(max_length=50, blank=True)  # Последнее решение
    dice_roll = models.IntegerField(default=1)  # Последний бросок кубика (1-6)
    
    # Навыки персонажа
    prototype_skill = models.IntegerField(default=0)  # Разработка прототипа
    presentation_skill = models.IntegerField(default=0)  # Презентации
    pitching_skill = models.IntegerField(default=0)  # Питчинг
    team_skill = models.IntegerField(default=0)  # Тимбилдинг
    marketing_skill = models.IntegerField(default=0)  # Маркетинг
    
    # Игровое состояние
    is_active = models.BooleanField(default=True)
    game_over = models.BooleanField(default=False)
    victory = models.BooleanField(default=False)
    game_paused = models.BooleanField(default=False)  # Пауза для событий
    
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


class EventTemplate(models.Model):
    """Шаблоны событий для админки"""
    key = models.CharField(max_length=50, unique=True, help_text="Уникальный ключ события (например: market_research)")
    title = models.CharField(max_length=200, help_text="Заголовок события")
    description = models.TextField(help_text="Описание ситуации")
    is_active = models.BooleanField(default=True, help_text="Активно ли событие")
    order = models.IntegerField(default=0, help_text="Порядок появления (меньше = раньше)")
    
    class Meta:
        verbose_name = 'Шаблон события'
        verbose_name_plural = 'Шаблоны событий'
        ordering = ['order', 'title']
    
    def __str__(self):
        return self.title


class EventChoice(models.Model):
    """Варианты выбора для событий"""
    event_template = models.ForeignKey(EventTemplate, on_delete=models.CASCADE, related_name='choices')
    choice_id = models.CharField(max_length=50, help_text="ID выбора (например: survey)")
    title = models.CharField(max_length=200, help_text="Текст кнопки")
    description = models.CharField(max_length=300, help_text="Краткое описание действия")
    
    # Затраты
    time_cost = models.IntegerField(default=1, help_text="Стоимость в днях (1 день = 1 минута)")
    money_cost = models.IntegerField(default=0, help_text="Стоимость в деньгах")
    
    # Эффекты
    money_effect = models.IntegerField(default=0, help_text="Изменение денег")
    reputation_effect = models.IntegerField(default=0, help_text="Изменение репутации")
    employees_effect = models.IntegerField(default=0, help_text="Изменение сотрудников")
    customers_effect = models.IntegerField(default=0, help_text="Изменение клиентов")
    
    # Навыки
    prototype_skill_effect = models.IntegerField(default=0, help_text="Изменение навыка разработки")
    presentation_skill_effect = models.IntegerField(default=0, help_text="Изменение навыка презентаций")
    pitching_skill_effect = models.IntegerField(default=0, help_text="Изменение навыка питчинга")
    team_skill_effect = models.IntegerField(default=0, help_text="Изменение навыка тимбилдинга")
    marketing_skill_effect = models.IntegerField(default=0, help_text="Изменение навыка маркетинга")
    
    # Связанные навыки (какие орбы могут появляться)
    skills = models.ManyToManyField('Skill', blank=True, verbose_name="Связанные навыки", help_text="Навыки, которые будут прокачиваться при этом выборе")
    
    # Стиль кнопки
    BUTTON_STYLES = [
        ('btn-primary', 'Синяя'),
        ('btn-secondary', 'Серая'),
        ('btn-success', 'Зеленая'),
        ('btn-danger', 'Красная'),
        ('btn-warning', 'Желтая'),
        ('btn-info', 'Голубая'),
    ]
    button_style = models.CharField(max_length=20, choices=BUTTON_STYLES, default='btn-primary')
    order = models.IntegerField(default=0, help_text="Порядок отображения")
    
    class Meta:
        verbose_name = 'Вариант выбора'
        verbose_name_plural = 'Варианты выбора'
        ordering = ['event_template', 'order', 'title']
    
    def __str__(self):
        return f"{self.event_template.title} - {self.title}"


class Skill(models.Model):
    """Модель для навыков, которые можно прокачивать в игре"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Ключ навыка", help_text="Уникальный ключ навыка (например: prototype)")
    display_name = models.CharField(max_length=100, verbose_name="Отображаемое название", help_text="Название для пользователя")
    color = models.CharField(max_length=7, default="#007bff", verbose_name="Цвет орба (HEX)", help_text="Цвет орба в формате #RRGGBB")
    icon = models.CharField(max_length=50, blank=True, verbose_name="Иконка (Bootstrap Icons)", help_text="Класс иконки Bootstrap Icons")
    description = models.TextField(blank=True, verbose_name="Описание навыка")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    order = models.IntegerField(default=0, verbose_name="Порядок отображения", help_text="Меньше = выше в списке")
    
    # Соответствие с полями в GameSession
    session_field = models.CharField(max_length=50, verbose_name="Поле в сессии", help_text="Название поля в GameSession (например: prototype_skill)")
    
    class Meta:
        verbose_name = "Навык"
        verbose_name_plural = "Навыки"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.display_name


class CompletedEvent(models.Model):
    """Завершенные события пользователя в игровой сессии"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='completed_events')
    event_template = models.ForeignKey(EventTemplate, on_delete=models.CASCADE, blank=True, null=True)  # Если событие из БД
    event_key = models.CharField(max_length=100, verbose_name="Ключ события")  # Для fallback событий
    choice_id = models.CharField(max_length=100, verbose_name="ID выбранного варианта", blank=True)
    completed_at = models.DateTimeField(auto_now_add=True)
    game_day = models.IntegerField(verbose_name="День игры когда произошло событие")
    
    class Meta:
        verbose_name = "Завершенное событие"
        verbose_name_plural = "Завершенные события"
        unique_together = ['session', 'event_key']  # Одно событие может быть пройдено только один раз в сессии
        ordering = ['-completed_at']
    
    def __str__(self):
        if self.event_template:
            return f"{self.session.company_name} - {self.event_template.title} (День {self.game_day})"
        return f"{self.session.company_name} - {self.event_key} (День {self.game_day})"