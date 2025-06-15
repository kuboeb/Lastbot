with open('templates/users.html', 'r') as f:
    content = f.read()

# Найдем место после deleteModal.show() и добавим обработчик подтверждения
js_code = '''
    // Обработчик кнопки подтверждения удаления
    document.getElementById('confirmDelete').addEventListener('click', async function() {
        if (!userIdToDelete) return;
        
        try {
            const response = await fetch(`/admin/users/${userIdToDelete}/delete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Успешно удалено
                alert(data.message || 'Пользователь удален');
                window.location.reload();
            } else {
                // Ошибка
                alert(data.error || 'Ошибка при удалении');
            }
        } catch (error) {
            alert('Ошибка: ' + error.message);
        }
        
        deleteModal.hide();
    });
'''

# Найдем место где заканчивается скрипт и добавим код
if 'confirmDelete' not in content:
    # Ищем место после deleteModal.show();
    insert_pos = content.find('deleteModal.show();')
    if insert_pos != -1:
        # Находим конец блока
        insert_pos = content.find('});', insert_pos) + 3
        content = content[:insert_pos] + '\n' + js_code + content[insert_pos:]

# Также убедимся что есть кнопка confirmDelete в модальном окне
if 'id="confirmDelete"' not in content:
    # Добавим id к кнопке подтверждения
    content = content.replace(
        '<button type="button" class="btn btn-danger">Удалить</button>',
        '<button type="button" class="btn btn-danger" id="confirmDelete">Удалить</button>'
    )

with open('templates/users.html', 'w') as f:
    f.write(content)

print("Updated users.html with delete functionality")
