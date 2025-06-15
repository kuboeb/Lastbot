// Функции для операторской панели

// Показать/скрыть загрузку
function showLoading(show = true) {
    if (show) {
        $('.loading-overlay').addClass('show');
    } else {
        $('.loading-overlay').removeClass('show');
    }
}

// Показать результат
function showResult(type, message) {
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle';
    
    const alert = $(`
        <div class="alert ${alertClass} alert-dismissible fade show result-message" role="alert">
            <i class="fas ${icon}"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `);
    
    $('body').append(alert);
    
    // Автоматически скрыть через 5 секунд
    setTimeout(function() {
        alert.alert('close');
    }, 5000);
}

// Валидация формы
function validateForm(mode) {
    if (mode === 'single') {
        const identifier = $('#identifier').val().trim();
        if (!identifier) {
            showResult('error', 'Введите идентификатор');
            return false;
        }
    } else {
        const identifiers = $('#identifiers').val().trim();
        if (!identifiers) {
            showResult('error', 'Введите хотя бы один идентификатор');
            return false;
        }
    }
    
    const message = $('#message').val().trim();
    if (!message) {
        showResult('error', 'Введите сообщение');
        return false;
    }
    
    if (message.length > 4096) {
        showResult('error', 'Сообщение слишком длинное (максимум 4096 символов)');
        return false;
    }
    
    return true;
}

// Быстрая вставка из буфера обмена
$(document).ready(function() {
    // Ctrl+V для массовой вставки
    $('#identifiers').on('paste', function(e) {
        setTimeout(function() {
            // Автоматически разделяем по строкам
            let content = $('#identifiers').val();
            content = content.replace(/[,;]/g, '\n');
            $('#identifiers').val(content);
        }, 100);
    });
    
    // Счетчик получателей для массовой рассылки
    $('#identifiers').on('input', function() {
        const lines = $(this).val().trim().split('\n').filter(line => line.trim());
        $('#recipientCount').text(lines.length);
    });
});

// Загрузка файла с получателями
function loadFromFile(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const content = e.target.result;
        $('#identifiers').val(content);
        $('#identifiers').trigger('input');
    };
    reader.readAsText(file);
}

// Проверка статуса отправки
function checkMessageStatus(messageId) {
    $.get(`/api/message/status/${messageId}`)
        .done(function(data) {
            if (data.delivered) {
                $(`#status-${messageId}`).html('<span class="badge bg-success">Доставлено</span>');
            }
        });
}
