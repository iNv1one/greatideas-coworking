from django.core.management.base import BaseCommand
from startup_game.models import Skill, EventTemplate, EventChoice


class Command(BaseCommand):
    help = 'Загружает тестовые события и навыки в базу данных'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Начинаем загрузку тестовых данных...'))
        
        # Создаем навыки
        self.create_skills()
        
        # Создаем события
        self.create_events()
        
        self.stdout.write(self.style.SUCCESS('✅ Тестовые данные успешно загружены!'))

    def create_skills(self):
        """Создает базовые навыки"""
        skills_data = [
            {
                'name': 'prototype',
                'display_name': 'Разработка прототипа',
                'color': '#28a745',
                'icon': '⚙️',
                'description': 'Навык создания прототипов и MVP',
                'session_field': 'prototype_skill',
                'order': 1
            },
            {
                'name': 'presentation',
                'display_name': 'Презентации',
                'color': '#007bff',
                'icon': '📊',
                'description': 'Навык создания и проведения презентаций',
                'session_field': 'presentation_skill',
                'order': 2
            },
            {
                'name': 'pitching',
                'display_name': 'Питчинг',
                'color': '#ffc107',
                'icon': '🎯',
                'description': 'Навык питчинга идей инвесторам',
                'session_field': 'pitching_skill',
                'order': 3
            },
            {
                'name': 'team',
                'display_name': 'Тимбилдинг',
                'color': '#6f42c1',
                'icon': '👥',
                'description': 'Навык работы с командой и найма сотрудников',
                'session_field': 'team_skill',
                'order': 4
            },
            {
                'name': 'marketing',
                'display_name': 'Маркетинг',
                'color': '#dc3545',
                'icon': '📈',
                'description': 'Навык продвижения и маркетинга',
                'session_field': 'marketing_skill',
                'order': 5
            }
        ]
        
        for skill_data in skills_data:
            skill, created = Skill.objects.get_or_create(
                name=skill_data['name'],
                defaults=skill_data
            )
            if created:
                self.stdout.write(f'✅ Создан навык: {skill.display_name}')
            else:
                self.stdout.write(f'⚠️ Навык уже существует: {skill.display_name}')

    def create_events(self):
        """Создает тестовые события"""
        
        # Получаем навыки для связывания
        prototype_skill = Skill.objects.get(name='prototype')
        presentation_skill = Skill.objects.get(name='presentation')
        pitching_skill = Skill.objects.get(name='pitching')
        team_skill = Skill.objects.get(name='team')
        marketing_skill = Skill.objects.get(name='marketing')
        
        events_data = [
            {
                'key': 'first_idea',
                'title': 'Первая идея',
                'description': 'У вас появилась отличная идея для стартапа! Как вы хотите её развивать?',
                'order': 1,
                'choices': [
                    {
                        'choice_id': 'research',
                        'title': 'Провести исследование рынка',
                        'description': 'Изучить конкурентов и потребности клиентов',
                        'time_cost': 2,
                        'money_cost': 100,
                        'reputation_effect': 5,
                        'button_style': 'btn-info',
                        'skills': [marketing_skill]
                    },
                    {
                        'choice_id': 'prototype',
                        'title': 'Сразу делать прототип',
                        'description': 'Начать разработку минимального продукта',
                        'time_cost': 3,
                        'money_cost': 200,
                        'prototype_skill_effect': 10,
                        'button_style': 'btn-success',
                        'skills': [prototype_skill]
                    },
                    {
                        'choice_id': 'team',
                        'title': 'Найти со-основателя',
                        'description': 'Поискать партнера для реализации идеи',
                        'time_cost': 1,
                        'money_cost': 0,
                        'employees_effect': 1,
                        'button_style': 'btn-warning',
                        'skills': [team_skill]
                    }
                ]
            },
            {
                'key': 'presentation_event',
                'title': 'Презентация проекта',
                'description': 'Вам нужно представить ваш проект. Выберите формат презентации.',
                'order': 2,
                'choices': [
                    {
                        'choice_id': 'formal_presentation',
                        'title': 'Формальная презентация',
                        'description': 'Подготовить детальную презентацию со слайдами',
                        'time_cost': 2,
                        'money_cost': 50,
                        'presentation_skill_effect': 15,
                        'reputation_effect': 10,
                        'button_style': 'btn-primary',
                        'skills': [presentation_skill]
                    },
                    {
                        'choice_id': 'pitch_demo',
                        'title': 'Питч с демо',
                        'description': 'Показать рабочий прототип и рассказать о продукте',
                        'time_cost': 1,
                        'money_cost': 0,
                        'pitching_skill_effect': 10,
                        'prototype_skill_effect': 5,
                        'customers_effect': 2,
                        'button_style': 'btn-success',
                        'skills': [pitching_skill, prototype_skill]
                    },
                    {
                        'choice_id': 'informal_meeting',
                        'title': 'Неформальная встреча',
                        'description': 'Организовать встречу в кафе для обсуждения идеи',
                        'time_cost': 1,
                        'money_cost': 25,
                        'reputation_effect': 3,
                        'team_skill_effect': 5,
                        'button_style': 'btn-secondary',
                        'skills': [team_skill]
                    }
                ]
            },
            {
                'key': 'funding_search',
                'title': 'Поиск финансирования',
                'description': 'Деньги заканчиваются. Как будете искать финансирование?',
                'order': 3,
                'choices': [
                    {
                        'choice_id': 'angel_investors',
                        'title': 'Ангельские инвесторы',
                        'description': 'Найти частных инвесторов для раннего этапа',
                        'time_cost': 3,
                        'money_cost': 100,
                        'money_effect': 5000,
                        'pitching_skill_effect': 20,
                        'button_style': 'btn-warning',
                        'skills': [pitching_skill, presentation_skill]
                    },
                    {
                        'choice_id': 'crowdfunding',
                        'title': 'Краудфандинг',
                        'description': 'Запустить кампанию на краудфандинговой платформе',
                        'time_cost': 2,
                        'money_cost': 200,
                        'money_effect': 2000,
                        'customers_effect': 10,
                        'button_style': 'btn-info',
                        'skills': [marketing_skill, presentation_skill]
                    },
                    {
                        'choice_id': 'bootstrap',
                        'title': 'Развиваться самостоятельно',
                        'description': 'Экономить и развиваться на собственные средства',
                        'time_cost': 1,
                        'money_cost': 0,
                        'money_effect': 500,
                        'reputation_effect': 5,
                        'button_style': 'btn-secondary',
                        'skills': [prototype_skill, team_skill]
                    }
                ]
            },
            {
                'key': 'product_development',
                'title': 'Развитие продукта',
                'description': 'Пора улучшать продукт. На чем сосредоточиться?',
                'order': 4,
                'choices': [
                    {
                        'choice_id': 'new_features',
                        'title': 'Новые функции',
                        'description': 'Добавить новые возможности в продукт',
                        'time_cost': 3,
                        'money_cost': 300,
                        'prototype_skill_effect': 15,
                        'customers_effect': 5,
                        'button_style': 'btn-success',
                        'skills': [prototype_skill]
                    },
                    {
                        'choice_id': 'user_experience',
                        'title': 'Улучшить UX',
                        'description': 'Сосредоточиться на удобстве использования',
                        'time_cost': 2,
                        'money_cost': 150,
                        'prototype_skill_effect': 10,
                        'customers_effect': 8,
                        'reputation_effect': 5,
                        'button_style': 'btn-primary',
                        'skills': [prototype_skill, marketing_skill]
                    },
                    {
                        'choice_id': 'marketing_push',
                        'title': 'Маркетинговая кампания',
                        'description': 'Сосредоточиться на привлечении клиентов',
                        'time_cost': 2,
                        'money_cost': 400,
                        'customers_effect': 15,
                        'reputation_effect': 10,
                        'button_style': 'btn-danger',
                        'skills': [marketing_skill, presentation_skill]
                    }
                ]
            },
            {
                'key': 'team_expansion',
                'title': 'Расширение команды',
                'description': 'Компания растет! Кого нанять в первую очередь?',
                'order': 5,
                'choices': [
                    {
                        'choice_id': 'developer',
                        'title': 'Разработчика',
                        'description': 'Нанять опытного программиста',
                        'time_cost': 2,
                        'money_cost': 500,
                        'employees_effect': 1,
                        'prototype_skill_effect': 10,
                        'button_style': 'btn-success',
                        'skills': [prototype_skill, team_skill]
                    },
                    {
                        'choice_id': 'marketer',
                        'title': 'Маркетолога',
                        'description': 'Нанять специалиста по маркетингу',
                        'time_cost': 2,
                        'money_cost': 400,
                        'employees_effect': 1,
                        'customers_effect': 8,
                        'button_style': 'btn-danger',
                        'skills': [marketing_skill, team_skill]
                    },
                    {
                        'choice_id': 'sales_manager',
                        'title': 'Менеджера по продажам',
                        'description': 'Нанять человека для работы с клиентами',
                        'time_cost': 1,
                        'money_cost': 350,
                        'employees_effect': 1,
                        'customers_effect': 10,
                        'money_effect': 200,
                        'button_style': 'btn-warning',
                        'skills': [pitching_skill, team_skill]
                    }
                ]
            }
        ]
        
        for event_data in events_data:
            choices_data = event_data.pop('choices')
            
            event_template, created = EventTemplate.objects.get_or_create(
                key=event_data['key'],
                defaults=event_data
            )
            
            if created:
                self.stdout.write(f'✅ Создано событие: {event_template.title}')
            else:
                self.stdout.write(f'⚠️ Событие уже существует: {event_template.title}')
            
            # Создаем варианты выбора
            for choice_data in choices_data:
                skills = choice_data.pop('skills', [])
                
                choice, choice_created = EventChoice.objects.get_or_create(
                    event_template=event_template,
                    choice_id=choice_data['choice_id'],
                    defaults=choice_data
                )
                
                if choice_created:
                    # Связываем навыки
                    choice.skills.set(skills)
                    self.stdout.write(f'  ✅ Создан выбор: {choice.title}')
                else:
                    self.stdout.write(f'  ⚠️ Выбор уже существует: {choice.title}')