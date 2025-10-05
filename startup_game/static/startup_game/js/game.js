// Startup Game JavaScript

// Игровые данные (будут обновляться с сервера)
let gameData = window.gameData || {
    money: 1000,
    reputation: 0,
    employees: 1,
    customers: 0,
    day: 1,
    level: 1
};

// API функция для игровых действий
async function gameAction(action, data = {}) {
    try {
        // Блокируем кнопки во время запроса
        setButtonsDisabled(true);
        
        const response = await fetch('/game/api/action/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value || getCookie('csrftoken')
            },
            body: JSON.stringify({
                action: action,
                ...data
            })
        });

        const result = await response.json();
        
        if (result.success) {
            // Обновляем игровые данные
            updateGameData(result);
            
            // Показываем сообщение если есть
            if (result.message) {
                showNotification(result.message, 'success');
            }
            
            // Показываем событие если есть
            if (result.event) {
                showEvent(result.event);
            }
            
            // Добавляем в лог
            addToGameLog(result);
            
        } else {
            showNotification(result.error || 'Произошла ошибка', 'error');
        }
        
    } catch (error) {
        console.error('Game action error:', error);
        showNotification('Ошибка соединения с сервером', 'error');
    } finally {
        // Разблокируем кнопки
        setButtonsDisabled(false);
    }
}

// Обновление игровых данных на странице
function updateGameData(data) {
    const fields = ['money', 'reputation', 'employees', 'customers', 'day', 'level'];
    
    fields.forEach(field => {
        if (data[field] !== undefined) {
            gameData[field] = data[field];
            const element = document.getElementById(field);
            if (element) {
                // Анимация изменения
                element.classList.add('stat-change');
                element.textContent = data[field];
                
                setTimeout(() => {
                    element.classList.remove('stat-change');
                }, 600);
            }
        }
    });
    
    // Обновляем стоимость найма
    updateHireCost();
    
    // Обновляем ежедневную статистику
    updateDailyStats();
    
    // Проверяем доступность кнопок
    updateButtonStates();
}

// Обновление стоимости найма сотрудника
function updateHireCost() {
    const hireCostElement = document.getElementById('hire-cost');
    if (hireCostElement) {
        const cost = 200 + (gameData.employees * 50);
        hireCostElement.textContent = cost;
    }
}

// Обновление ежедневной статистики
function updateDailyStats() {
    const dailyIncomeElement = document.getElementById('daily-income');
    const dailyExpensesElement = document.getElementById('daily-expenses');
    
    if (dailyIncomeElement) {
        const income = gameData.customers * 10;
        dailyIncomeElement.textContent = income + '$';
    }
    
    if (dailyExpensesElement) {
        const expenses = gameData.employees * 50;
        dailyExpensesElement.textContent = expenses + '$';
    }
}

// Проверка доступности кнопок
function updateButtonStates() {
    const hireCost = 200 + (gameData.employees * 50);
    const marketingCost = 300;
    const officeCost = 500;
    
    // Кнопка найма
    const hireBtn = document.getElementById('hire-btn');
    if (hireBtn) {
        hireBtn.disabled = gameData.money < hireCost;
    }
    
    // Кнопка маркетинга
    const marketingBtn = document.getElementById('marketing-btn');
    if (marketingBtn) {
        marketingBtn.disabled = gameData.money < marketingCost;
    }
    
    // Кнопка улучшения офиса
    const officeBtn = document.getElementById('office-btn');
    if (officeBtn) {
        officeBtn.disabled = gameData.money < officeCost;
    }
}

// Блокировка/разблокировка кнопок
function setButtonsDisabled(disabled) {
    const buttons = document.querySelectorAll('.action-btn');
    buttons.forEach(btn => {
        btn.disabled = disabled;
    });
}

// Показ уведомления
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `game-notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${getIconForType(type)} me-2"></i>
        ${message}
    `;
    
    document.body.appendChild(notification);
    
    // Автоматическое скрытие через 4 секунды
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 4000);
}

// Получение иконки для типа уведомления
function getIconForType(type) {
    switch (type) {
        case 'success': return 'check-circle';
        case 'error': return 'exclamation-circle';
        case 'warning': return 'exclamation-triangle';
        default: return 'info-circle';
    }
}

// Показ игрового события
function showEvent(event) {
    const modal = document.getElementById('eventModal');
    if (!modal) return;
    
    const title = modal.querySelector('#eventTitle');
    const description = modal.querySelector('#eventDescription');
    const effects = modal.querySelector('#eventEffects');
    
    if (title) title.textContent = event.title;
    if (description) description.textContent = event.description;
    
    // Показываем эффекты события
    if (effects) {
        let effectsHtml = '<div class="event-effects">';
        
        if (event.money_change) {
            const sign = event.money_change > 0 ? '+' : '';
            const color = event.money_change > 0 ? 'success' : 'danger';
            effectsHtml += `<div class="text-${color}"><i class="fas fa-dollar-sign"></i> ${sign}${event.money_change}$ Деньги</div>`;
        }
        
        if (event.reputation_change) {
            const sign = event.reputation_change > 0 ? '+' : '';
            const color = event.reputation_change > 0 ? 'success' : 'danger';
            effectsHtml += `<div class="text-${color}"><i class="fas fa-star"></i> ${sign}${event.reputation_change} Репутация</div>`;
        }
        
        if (event.customers_change) {
            const sign = event.customers_change > 0 ? '+' : '';
            const color = event.customers_change > 0 ? 'success' : 'danger';
            effectsHtml += `<div class="text-${color}"><i class="fas fa-user-friends"></i> ${sign}${event.customers_change} Клиенты</div>`;
        }
        
        if (event.employees_change) {
            const sign = event.employees_change > 0 ? '+' : '';
            const color = event.employees_change > 0 ? 'success' : 'danger';
            effectsHtml += `<div class="text-${color}"><i class="fas fa-users"></i> ${sign}${event.employees_change} Сотрудники</div>`;
        }
        
        effectsHtml += '</div>';
        effects.innerHTML = effectsHtml;
    }
    
    // Показываем модальное окно
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

// Добавление записи в игровой лог
function addToGameLog(data) {
    const gameLog = document.getElementById('game-log');
    if (!gameLog) return;
    
    let message = '';
    let type = 'info';
    
    if (data.daily_income !== undefined) {
        message = `День ${data.day}: Доход ${data.daily_income}$, Расходы ${data.daily_expenses}$`;
        type = data.daily_income > data.daily_expenses ? 'success' : 'warning';
    } else if (data.message) {
        message = data.message;
        type = 'success';
    }
    
    if (message) {
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        logEntry.innerHTML = `
            <i class="fas fa-${getIconForType(type)} me-2"></i>
            ${message}
        `;
        
        gameLog.insertBefore(logEntry, gameLog.firstChild);
        
        // Ограничиваем количество записей
        const entries = gameLog.querySelectorAll('.log-entry');
        if (entries.length > 10) {
            entries[entries.length - 1].remove();
        }
    }
}

// Получение CSRF токена из cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Обновляем состояние кнопок
    updateButtonStates();
    updateHireCost();
    updateDailyStats();
    
    // Добавляем приветственное сообщение в лог
    addToGameLog({
        message: 'Игра началась! Удачи в развитии вашего стартапа!'
    });
});