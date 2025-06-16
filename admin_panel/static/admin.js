// Функции для админ панели

// Экспорт в Excel
function exportToExcel(type) {
    const params = new URLSearchParams(window.location.search);
    params.append('export', 'excel');
    params.append('type', type);
    
    window.location.href = `/admin/export?${params.toString()}`;
}

// Автообновление статистики
function updateStats() {
    $.get('/admin/api/stats/realtime')
        .done(function(data) {
            $('#online-users').text(data.online_users);
            $('#today-applications').text(data.today_applications);
            $('#today-referrals').text(data.today_referrals);
        });
}

// Обновляем каждые 30 секунд
setInterval(updateStats, 30000);

// График в реальном времени
function initRealtimeChart() {
    const ctx = document.getElementById('realtimeChart');
    if (!ctx) return;
    
    const chart = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Активные пользователи',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
    
    // Обновление данных
    setInterval(function() {
        $.get('/admin/api/stats/active-users')
            .done(function(data) {
                const now = new Date().toLocaleTimeString();
                chart.data.labels.push(now);
                chart.data.datasets[0].data.push(data.count);
                
                // Оставляем только последние 20 точек
                if (chart.data.labels.length > 20) {
                    chart.data.labels.shift();
                    chart.data.datasets[0].data.shift();
                }
                
                chart.update();
            });
    }, 5000);
}

// Инициализация при загрузке
$(document).ready(function() {
    initRealtimeChart();
    
    // Tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // Подтверждение удаления
    $('.delete-btn').click(function(e) {
        if (!confirm('Вы уверены?')) {
            e.preventDefault();
        }
    });
});

// Функция удаления пользователя с подтверждением
function deleteUser(userId, username) {
    if (confirm(`ВНИМАНИЕ! Вы уверены, что хотите удалить пользователя ${username ? '@' + username : 'ID: ' + userId}?\n\nБудут удалены:\n- Все заявки пользователя\n- История действий\n- Данные о конверсиях\n- Все связанные записи\n\nЭто действие НЕЛЬЗЯ отменить!`)) {
        
        // Второе подтверждение для защиты
        if (confirm('Это последнее предупреждение! Точно удалить?')) {
            $.ajax({
                url: '/admin/users/delete',
                method: 'POST',
                data: { user_id: userId },
                success: function(response) {
                    if (response.success) {
                        alert(response.message);
                        // Удаляем строку из таблицы
                        $(`tr[data-user-id="${userId}"]`).fadeOut(300, function() {
                            $(this).remove();
                        });
                    } else {
                        alert('Ошибка: ' + response.error);
                    }
                },
                error: function() {
                    alert('Ошибка при удалении пользователя');
                }
            });
        }
    }
}
