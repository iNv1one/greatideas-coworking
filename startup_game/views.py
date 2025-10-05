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
def game_play(request):
    """Основная игровая страница"""
    # Получаем или создаем игровую сессию
    session, created = GameSession.objects.get_or_create(
        user=request.user,
        is_active=True,
        defaults={
            'company_name': f"{request.user.username}'s Startup",
            'money': 1000,
            'reputation': 0,
            'employees': 1,
            'customers': 0,
            'day': 1,
            'level': 1,
        }
    )
    
    # Расчеты для отображения
    daily_income = session.customers * 10
    daily_expenses = session.employees * 50
    daily_profit = daily_income - daily_expenses
    hire_cost = 200 + (session.employees * 50)
    
    context = {
        'session': session,
        'page_title': f'{session.company_name} - Day {session.day}',
        'daily_income': daily_income,
        'daily_expenses': daily_expenses,
        'daily_profit': daily_profit,
        'hire_cost': hire_cost,
    }
    return render(request, 'startup_game/play.html', context)


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
        is_active=True
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