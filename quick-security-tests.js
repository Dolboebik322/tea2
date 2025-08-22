// 🚀 Быстрые тесты безопасности для консоли браузера
// ⚠️ ТОЛЬКО для сайтов, на которые у вас есть разрешение!

console.log('🚀 Быстрые тесты безопасности загружены');

// Быстрая проверка XSS уязвимостей
function quickXSSTest() {
    console.log('🔍 Быстрая проверка XSS...');
    
    const testPayloads = [
        '<script>console.log("XSS-FOUND")</script>',
        '"><img src=x onerror=console.log("XSS")>',
        "';alert('XSS');//"
    ];
    
    const inputs = document.querySelectorAll('input[type="text"], textarea');
    let foundVulns = 0;
    
    inputs.forEach((input, index) => {
        const originalValue = input.value;
        
        testPayloads.forEach(payload => {
            input.value = payload;
            input.dispatchEvent(new Event('input', { bubbles: true }));
            
            // Проверяем отражение
            if (document.body.innerHTML.includes(payload)) {
                console.warn(`⚠️  XSS найден в поле ${index + 1}: ${input.name || input.id}`);
                foundVulns++;
            }
        });
        
        input.value = originalValue;
    });
    
    if (foundVulns === 0) {
        console.log('✅ XSS уязвимости не обнаружены');
    }
    
    return foundVulns;
}

// Проверка заголовков безопасности (упрощенная)
function quickHeaderCheck() {
    console.log('🔒 Проверка заголовков...');
    
    const criticalHeaders = ['Content-Security-Policy', 'X-Frame-Options'];
    
    fetch(location.href, { method: 'HEAD' })
        .then(response => {
            criticalHeaders.forEach(header => {
                if (response.headers.get(header)) {
                    console.log(`✅ ${header}: присутствует`);
                } else {
                    console.warn(`❌ ${header}: ОТСУТСТВУЕТ!`);
                }
            });
        })
        .catch(() => console.log('❌ Не удалось проверить заголовки'));
}

// Поиск потенциально опасных форм
function findRiskyForms() {
    console.log('📋 Поиск потенциально опасных форм...');
    
    const forms = document.querySelectorAll('form');
    let riskyForms = 0;
    
    forms.forEach((form, index) => {
        const method = form.method.toLowerCase();
        const hasFileUpload = form.querySelector('input[type="file"]');
        const hasTextFields = form.querySelectorAll('input[type="text"], textarea').length;
        
        console.log(`Форма ${index + 1}:`);
        console.log(`  Метод: ${method}`);
        console.log(`  Текстовых полей: ${hasTextFields}`);
        console.log(`  Загрузка файлов: ${hasFileUpload ? 'Да' : 'Нет'}`);
        
        if (method === 'get' && hasTextFields > 0) {
            console.warn('  ⚠️  GET форма с текстовыми полями - потенциальный риск');
            riskyForms++;
        }
        
        if (hasFileUpload) {
            console.warn('  ⚠️  Форма с загрузкой файлов - проверьте валидацию');
            riskyForms++;
        }
    });
    
    return riskyForms;
}

// Быстрая проверка cookies
function quickCookieCheck() {
    console.log('🍪 Быстрая проверка cookies...');
    
    if (!document.cookie) {
        console.log('ℹ️  Cookies не найдены');
        return;
    }
    
    const cookies = document.cookie.split(';');
    let insecureCookies = 0;
    
    cookies.forEach(cookie => {
        const cookieName = cookie.trim().split('=')[0];
        
        // Простая проверка (полная проверка требует доступа к заголовкам Set-Cookie)
        if (!cookie.includes('Secure') && location.protocol === 'https:') {
            console.warn(`⚠️  Cookie "${cookieName}" может быть без Secure флага`);
            insecureCookies++;
        }
    });
    
    if (insecureCookies === 0) {
        console.log('✅ Явных проблем с cookies не найдено');
    }
    
    return insecureCookies;
}

// Проверка на CVE-2024-3566 специфичные паттерны
function checkBatBadBut() {
    console.log('🦇 Проверка на BatBadBut (CVE-2024-3566) паттерны...');
    
    const inputs = document.querySelectorAll('input[type="text"], textarea');
    const testPayloads = [
        'test" && echo "vulnerable" && echo "',
        'package" | whoami | echo "',
        'file.exe" & echo "test" & echo "'
    ];
    
    let foundIssues = 0;
    
    inputs.forEach((input, index) => {
        const originalValue = input.value;
        
        testPayloads.forEach(payload => {
            input.value = payload;
            
            // Проверяем, есть ли отражение payload'а
            setTimeout(() => {
                if (document.body.innerHTML.includes('vulnerable') || 
                    document.body.innerHTML.includes('whoami') ||
                    document.body.innerHTML.includes(payload)) {
                    console.warn(`⚠️  Возможная уязвимость BatBadBut в поле ${index + 1}`);
                    foundIssues++;
                }
            }, 100);
        });
        
        input.value = originalValue;
    });
    
    setTimeout(() => {
        if (foundIssues === 0) {
            console.log('✅ BatBadBut уязвимости не обнаружены');
        }
    }, 500);
    
    return foundIssues;
}

// Быстрое полное сканирование
function quickFullScan() {
    console.log('🚀 БЫСТРОЕ ПОЛНОЕ СКАНИРОВАНИЕ');
    console.log('==============================');
    
    const results = {
        xss: quickXSSTest(),
        forms: findRiskyForms(),
        cookies: quickCookieCheck(),
        batbad: checkBatBadBut()
    };
    
    quickHeaderCheck();
    
    setTimeout(() => {
        console.log('\n📊 КРАТКИЙ ОТЧЕТ:');
        console.log(`XSS проблем: ${results.xss}`);
        console.log(`Рискованных форм: ${results.forms}`);
        console.log(`Проблем с cookies: ${results.cookies}`);
        console.log(`BatBadBut проблем: ${results.batbad}`);
        
        const total = results.xss + results.forms + results.cookies + results.batbad;
        
        if (total === 0) {
            console.log('✅ Серьезных проблем не обнаружено в быстром сканировании');
        } else {
            console.log(`⚠️  Найдено ${total} потенциальных проблем`);
            console.log('💡 Рекомендуется провести более детальное тестирование');
        }
    }, 1000);
    
    return results;
}

// Генератор отчета для отправки другу
function generateReport() {
    console.log('📝 Генерация отчета...');
    
    const siteUrl = window.location.href;
    const timestamp = new Date().toISOString();
    
    const report = `
🛡️ ОТЧЕТ О БЕЗОПАСНОСТИ САЙТА
============================
URL: ${siteUrl}
Дата: ${timestamp}
Тестировщик: Дружеское тестирование

РЕЗУЛЬТАТЫ БЫСТРОГО СКАНИРОВАНИЯ:
${quickFullScan()}

РЕКОМЕНДАЦИИ:
1. Проверьте валидацию всех пользовательских данных
2. Убедитесь в наличии заголовков безопасности
3. Используйте HTTPS для всех страниц
4. Проверьте настройки cookies
5. Рассмотрите внедрение Content Security Policy

⚠️ ВАЖНО: Это базовое тестирование. Рекомендуется 
провести профессиональный аудит безопасности.
    `;
    
    console.log(report);
    
    // Копируем в буфер обмена (если поддерживается)
    if (navigator.clipboard) {
        navigator.clipboard.writeText(report).then(() => {
            console.log('📋 Отчет скопирован в буфер обмена');
        });
    }
    
    return report;
}

// Экспорт функций
window.QuickSecurity = {
    quickXSSTest,
    quickHeaderCheck,
    findRiskyForms,
    quickCookieCheck,
    checkBatBadBut,
    quickFullScan,
    generateReport
};

console.log('\n📋 БЫСТРЫЕ КОМАНДЫ:');
console.log('QuickSecurity.quickFullScan()    - Быстрое полное сканирование');
console.log('QuickSecurity.quickXSSTest()     - Только XSS тест');
console.log('QuickSecurity.quickHeaderCheck() - Только заголовки');
console.log('QuickSecurity.checkBatBadBut()   - Только CVE-2024-3566');
console.log('QuickSecurity.generateReport()   - Создать отчет для друга');

console.log('\n🚀 Быстрый старт: QuickSecurity.quickFullScan()');
console.log('📝 Для отчета: QuickSecurity.generateReport()');