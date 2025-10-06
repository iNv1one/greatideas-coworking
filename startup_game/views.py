from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import json
import random
from .models import GameSession, GameEvent, Achievement, UserAchievement


def game_home(request):
    """Главная страница игры"""
    context = {
        'page_title': 'Startup Simulator - Создай свой стартап!',
        'page_description': 'Интерактивная игра о создании стартапа с нуля до успеха'
    }
    return render(request, 'startup_game/home.html', context)


@login_required
def company_name(request):
    """Страница выбора названия компании"""
    if request.method == 'POST':
        company_name = request.POST.get('company_name', '').strip()
        if company_name:
            # Сохраняем название в сессии и переходим к выбору отрасли
            request.session['new_company_name'] = company_name
            return redirect('startup_game:industry_select')
    
    context = {
        'page_title': 'Название компании - Startup Simulator',
        'default_name': f"{request.user.username}'s Startup"
    }
    return render(request, 'startup_game/company_name.html', context)


@login_required
def industry_select(request):
    """Страница выбора отрасли"""
    company_name = request.session.get('new_company_name')
    if not company_name:
        return redirect('startup_game:company_name')
    
    if request.method == 'POST':
        industry = request.POST.get('industry', '').strip()
        if industry:
            # Завершаем текущие активные сессии
            GameSession.objects.filter(user=request.user, is_active=True).update(is_active=False)
            
            # Создаем новую игровую сессию
            session = GameSession.objects.create(
                user=request.user,
                company_name=company_name,
                industry=industry,
                money=500,  # Стартовая сумма 500$
                reputation=0,
                employees=1,
                customers=0,
                day=1,
                level=1,
                game_time=480,  # 8:00 утра
                is_active=True,
                game_paused=False,
                # Сбрасываем все навыки в 0 для новой игры
                prototype_skill=0,
                presentation_skill=0,
                pitching_skill=0,
                team_skill=0
            )
            
            # Очищаем временные данные из сессии
            if 'new_company_name' in request.session:
                del request.session['new_company_name']
            
            return redirect('startup_game:play')
    
    context = {
        'page_title': 'Выбор отрасли - Startup Simulator',
        'company_name': company_name
    }
    return render(request, 'startup_game/industry_select.html', context)


@login_required
def game_play(request):
    """Основная игровая страница"""
    try:
        # Проверяем есть ли активная сессия
        try:
            session = GameSession.objects.get(user=request.user, is_active=True)
        except GameSession.DoesNotExist:
            # Если нет активной сессии, показываем этапы создания компании
            session = None
        
        # Если это POST запрос для создания новой компании
        if request.method == 'POST':
            if not session:
                company_name = request.POST.get('company_name', '').strip()
                industry = request.POST.get('industry', '').strip()
                
                if company_name and industry:
                    # Завершаем все старые сессии
                    GameSession.objects.filter(user=request.user, is_active=True).update(is_active=False)
                    
                    # Создаем новую сессию с базовыми полями
                    defaults = {
                        'company_name': company_name,
                        'money': 500,
                        'reputation': 0,
                        'employees': 1,
                        'customers': 0,
                        'day': 1,
                        'level': 1,
                    }
                    
                    # Добавляем новые поля если они есть в модели
                    try:
                        # Проверяем наличие полей через модель Django
                        model_fields = [field.name for field in GameSession._meta.get_fields()]
                        
                        if 'industry' in model_fields:
                            defaults['industry'] = industry
                        if 'game_time' in model_fields:
                            defaults['game_time'] = 480
                        if 'game_paused' in model_fields:
                            defaults['game_paused'] = False
                        if 'last_event_day' in model_fields:
                            defaults['last_event_day'] = 0
                        if 'dice_roll' in model_fields:
                            defaults['dice_roll'] = 1
                        # Сбрасываем навыки для новой игры
                        if 'prototype_skill' in model_fields:
                            defaults['prototype_skill'] = 0
                        if 'presentation_skill' in model_fields:
                            defaults['presentation_skill'] = 0
                        if 'pitching_skill' in model_fields:
                            defaults['pitching_skill'] = 0
                        if 'team_skill' in model_fields:
                            defaults['team_skill'] = 0
                    except:
                        pass  # Игнорируем ошибки с базой данных
                    
                    session = GameSession.objects.create(user=request.user, is_active=True, **defaults)
                    
                    return JsonResponse({'success': True, 'redirect': True})
        
        # Расчеты для отображения (только если есть сессия)
        if session:
            daily_income = session.customers * 10
            daily_expenses = session.employees * 50
            daily_profit = daily_income - daily_expenses
            hire_cost = 200 + (session.employees * 50)
            page_title = f'{session.company_name} - Day {session.day}'
        else:
            daily_income = daily_expenses = daily_profit = hire_cost = 0
            page_title = 'Создание стартапа'
        
        # Подготавливаем данные сессии для JSON
        session_data = None
        if session:
            session_data = {
                'id': session.id,
                'company_name': session.company_name,
                'money': session.money,
                'reputation': session.reputation,
                'employees': session.employees,
                'customers': session.customers,
                'day': session.day,
                'level': session.level,
                'is_active': session.is_active,
                'game_over': session.game_over,
                'victory': session.victory,
            }
            
            # Добавляем новые поля если они есть
            if hasattr(session, 'industry'):
                session_data['industry'] = session.industry
            if hasattr(session, 'game_time'):
                session_data['game_time'] = session.game_time
            if hasattr(session, 'game_paused'):
                session_data['game_paused'] = session.game_paused
            if hasattr(session, 'last_event_day'):
                session_data['last_event_day'] = session.last_event_day
            if hasattr(session, 'dice_roll'):
                session_data['dice_roll'] = session.dice_roll
            
            # Добавляем навыки из базы данных
            session_data['skills'] = {
                'prototype': getattr(session, 'prototype_skill', 0),
                'presentation': getattr(session, 'presentation_skill', 0),
                'pitching': getattr(session, 'pitching_skill', 0),
                'team': getattr(session, 'team_skill', 0)
            }
        
        context = {
            'session': session,
            'session_data': session_data,
            'page_title': page_title,
            'daily_income': daily_income,
            'daily_expenses': daily_expenses,
            'daily_profit': daily_profit,
            'hire_cost': hire_cost,
        }
        return render(request, 'startup_game/play_clean.html', context)
    
    except Exception as e:
        # В случае любой ошибки показываем простую страницу создания игры
        context = {
            'session': None,
            'session_data': None,
            'page_title': 'Создание стартапа',
            'daily_income': 0,
            'daily_expenses': 0,
            'daily_profit': 0,
            'hire_cost': 0,
            'error_message': str(e) if request.user.is_staff else None,  # Показываем ошибку только админам
        }
        return render(request, 'startup_game/play_clean.html', context)


@login_required
@csrf_exempt
def sync_time(request):
    """API для синхронизации игрового времени"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            game_time = data.get('game_time', 480)
            day = data.get('day', 1)
            
            # Обновляем активную сессию пользователя
            session = GameSession.objects.filter(user=request.user, is_active=True).first()
            if session:
                session.game_time = game_time
                session.day = day
                session.save()
                
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})


@login_required
@csrf_exempt
def process_choice(request):
    """API для обработки выборов игрока"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            choice = data.get('choice', '')
            dice_roll = data.get('dice_roll', 1)
            money = data.get('money', 500)
            
            # Обновляем активную сессию пользователя
            session = GameSession.objects.filter(user=request.user, is_active=True).first()
            if session:
                session.last_decision = choice
                session.dice_roll = dice_roll
                session.money = money
                session.game_paused = False
                session.save()
                
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})


@login_required
def new_game(request):
    """Начать новую игру"""
    # Завершаем текущую активную сессию
    GameSession.objects.filter(user=request.user, is_active=True).update(is_active=False)
    
    # Создаем новую сессию
    company_name = request.POST.get('company_name', f"{request.user.username}'s Startup")
    
    session = GameSession.objects.create(
        user=request.user,
        company_name=company_name,
        money=1000,
        reputation=0,
        employees=1,
        customers=0,
        day=1,
        level=1,
        is_active=True,
        # Сбрасываем все навыки в 0 для новой игры
        prototype_skill=0,
        presentation_skill=0,
        pitching_skill=0,
        team_skill=0
    )
    
    return redirect('startup_game:play')


@login_required
@csrf_exempt
def game_action(request):
    """API для игровых действий"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        action = data.get('action')
        
        session = get_object_or_404(GameSession, user=request.user, is_active=True)
        
        if action == 'next_day':
            return handle_next_day(session)
        elif action == 'hire_employee':
            return handle_hire_employee(session)
        elif action == 'marketing_campaign':
            return handle_marketing_campaign(session)
        elif action == 'upgrade_office':
            return handle_upgrade_office(session)
        else:
            return JsonResponse({'error': 'Unknown action'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def handle_next_day(session):
    """Обработка перехода к следующему дню"""
    session.day += 1
    
    # Ежедневный доход
    daily_income = session.customers * 10 + random.randint(0, 100)
    session.money += daily_income
    
    # Расходы на сотрудников
    daily_expenses = session.employees * 50
    session.money -= daily_expenses
    
    # Случайные события
    event_chance = random.random()
    event_data = None
    
    if event_chance < 0.3:  # 30% шанс события
        event_data = generate_random_event(session)
    
    session.save()
    
    response_data = {
        'success': True,
        'day': session.day,
        'money': session.money,
        'reputation': session.reputation,
        'employees': session.employees,
        'customers': session.customers,
        'daily_income': daily_income,
        'daily_expenses': daily_expenses,
    }
    
    if event_data:
        response_data['event'] = event_data
    
    return JsonResponse(response_data)


def handle_hire_employee(session):
    """Найм сотрудника"""
    cost = 200 + (session.employees * 50)  # Стоимость растет с количеством сотрудников
    
    if session.money < cost:
        return JsonResponse({'error': 'Недостаточно денег'}, status=400)
    
    session.money -= cost
    session.employees += 1
    session.save()
    
    # Создаем событие
    GameEvent.objects.create(
        session=session,
        event_type='decision',
        title='Нанят новый сотрудник',
        description=f'Вы наняли нового сотрудника за {cost}$. Теперь у вас {session.employees} сотрудников.',
        day_occurred=session.day,
        money_change=-cost,
        employees_change=1
    )
    
    return JsonResponse({
        'success': True,
        'money': session.money,
        'employees': session.employees,
        'message': f'Нанят новый сотрудник! Стоимость: {cost}$'
    })


def handle_marketing_campaign(session):
    """Маркетинговая кампания"""
    cost = 300
    
    if session.money < cost:
        return JsonResponse({'error': 'Недостаточно денег'}, status=400)
    
    session.money -= cost
    new_customers = random.randint(5, 15)
    reputation_gain = random.randint(1, 3)
    
    session.customers += new_customers
    session.reputation += reputation_gain
    session.save()
    
    # Создаем событие
    GameEvent.objects.create(
        session=session,
        event_type='decision',
        title='Маркетинговая кампания',
        description=f'Ваша маркетинговая кампания привлекла {new_customers} новых клиентов и повысила репутацию на {reputation_gain}.',
        day_occurred=session.day,
        money_change=-cost,
        customers_change=new_customers,
        reputation_change=reputation_gain
    )
    
    return JsonResponse({
        'success': True,
        'money': session.money,
        'customers': session.customers,
        'reputation': session.reputation,
        'message': f'Кампания успешна! +{new_customers} клиентов, +{reputation_gain} репутации'
    })


def handle_upgrade_office(session):
    """Улучшение офиса"""
    cost = 500
    
    if session.money < cost:
        return JsonResponse({'error': 'Недостаточно денег'}, status=400)
    
    session.money -= cost
    reputation_gain = random.randint(2, 5)
    session.reputation += reputation_gain
    session.save()
    
    # Создаем событие
    GameEvent.objects.create(
        session=session,
        event_type='decision',
        title='Улучшение офиса',
        description=f'Вы улучшили офис, что повысило репутацию компании на {reputation_gain}.',
        day_occurred=session.day,
        money_change=-cost,
        reputation_change=reputation_gain
    )
    
    return JsonResponse({
        'success': True,
        'money': session.money,
        'reputation': session.reputation,
        'message': f'Офис улучшен! +{reputation_gain} репутации'
    })


def generate_random_event(session):
    """Генерация случайного события"""
    events = [
        {
            'type': 'opportunity',
            'title': 'Крупный клиент',
            'description': 'К вам обратился крупный клиент с выгодным предложением!',
            'money_change': random.randint(200, 500),
            'customers_change': random.randint(2, 5),
        },
        {
            'type': 'challenge',
            'title': 'Конкуренты',
            'description': 'Конкуренты запустили агрессивную маркетинговую кампанию.',
            'customers_change': -random.randint(1, 3),
            'reputation_change': -random.randint(1, 2),
        },
        {
            'type': 'news',
            'title': 'Положительные отзывы',
            'description': 'В прессе появились положительные отзывы о вашей компании!',
            'reputation_change': random.randint(2, 4),
            'customers_change': random.randint(1, 3),
        },
    ]
    
    event_data = random.choice(events)
    
    # Применяем изменения
    session.money += event_data.get('money_change', 0)
    session.reputation += event_data.get('reputation_change', 0)
    session.customers += event_data.get('customers_change', 0)
    session.employees += event_data.get('employees_change', 0)
    
    # Создаем запись события
    GameEvent.objects.create(
        session=session,
        event_type=event_data['type'],
        title=event_data['title'],
        description=event_data['description'],
        day_occurred=session.day,
        money_change=event_data.get('money_change', 0),
        reputation_change=event_data.get('reputation_change', 0),
        customers_change=event_data.get('customers_change', 0),
        employees_change=event_data.get('employees_change', 0),
    )
    
    return event_data


@login_required
@csrf_exempt
def game_skill_api(request):
    """API для сохранения навыков"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        skill_type = data.get('skill_type')
        value = data.get('value')
        
        if not skill_type or value is None:
            return JsonResponse({'error': 'Missing skill_type or value'}, status=400)
        
        session = get_object_or_404(GameSession, user=request.user, is_active=True)
        
        # Обновляем соответствующий навык
        if skill_type == 'prototype':
            session.prototype_skill = value
        elif skill_type == 'presentation':
            session.presentation_skill = value
        elif skill_type == 'pitching':
            session.pitching_skill = value
        elif skill_type == 'team':
            session.team_skill = value
        else:
            return JsonResponse({'error': 'Invalid skill_type'}, status=400)
        
        session.save()
        
        return JsonResponse({
            'success': True,
            'skill_type': skill_type,
            'value': value
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt  
def get_events_api(request):
    """API для получения событий из базы данных"""
    from .models import EventTemplate, Skill
    
    events = EventTemplate.objects.filter(is_active=True).prefetch_related('choices__skills').order_by('order')
    
    events_data = {}
    for event in events:
        choices_data = []
        for choice in event.choices.all().order_by('order'):
            # Создаем объект эффектов
            effects = {}
            if choice.money_effect != 0:
                effects['money'] = choice.money_effect
            if choice.reputation_effect != 0:
                effects['reputation'] = choice.reputation_effect
            if choice.employees_effect != 0:
                effects['employees'] = choice.employees_effect
            if choice.customers_effect != 0:
                effects['customers'] = choice.customers_effect
            if choice.prototype_skill_effect != 0:
                effects['prototype_skill'] = choice.prototype_skill_effect
            if choice.presentation_skill_effect != 0:
                effects['presentation_skill'] = choice.presentation_skill_effect
            if choice.pitching_skill_effect != 0:
                effects['pitching_skill'] = choice.pitching_skill_effect
            if choice.team_skill_effect != 0:
                effects['team_skill'] = choice.team_skill_effect
            if choice.marketing_skill_effect != 0:
                effects['marketing_skill'] = choice.marketing_skill_effect
            
            # Получаем связанные навыки
            related_skills = []
            for skill in choice.skills.filter(is_active=True).order_by('order'):
                related_skills.append({
                    'name': skill.name,
                    'displayName': skill.display_name,
                    'color': skill.color,
                    'icon': skill.icon,
                    'sessionField': skill.session_field
                })
            
            choices_data.append({
                'id': choice.choice_id,
                'text': choice.title,
                'description': choice.description,
                'timeCost': choice.time_cost,
                'moneyCost': choice.money_cost,
                'effects': effects,
                'buttonStyle': choice.button_style,
                'skills': related_skills  # Добавляем информацию о навыках
            })
        
        events_data[event.key] = {
            'title': event.title,
            'description': event.description,
            'choices': choices_data
        }
    
    # Получаем все доступные навыки из базы данных
    all_skills = Skill.objects.filter(is_active=True).order_by('order')
    skills_data = []
    for skill in all_skills:
        skills_data.append({
            'name': skill.name,
            'displayName': skill.display_name,
            'color': skill.color,
            'icon': skill.icon,
            'sessionField': skill.session_field,
            'type': skill.session_field  # Добавляем type для совместимости с JavaScript
        })
    
    return JsonResponse({
        'events': events_data,
        'availableSkills': skills_data  # Добавляем список всех доступных навыков
    })


@login_required
def game_stats(request):
    """Статистика игры"""
    sessions = GameSession.objects.filter(user=request.user).order_by('-updated_at')
    achievements = UserAchievement.objects.filter(user=request.user).select_related('achievement')
    
    context = {
        'sessions': sessions,
        'achievements': achievements,
        'page_title': 'Статистика игры',
    }
    return render(request, 'startup_game/stats.html', context)