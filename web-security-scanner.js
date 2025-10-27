// 🛡️ Этичный сканер безопасности веб-форм
// ⚠️ ИСПОЛЬЗУЙТЕ ТОЛЬКО НА САЙТАХ, КОТОРЫМИ ВЫ ВЛАДЕЕТЕ ИЛИ ИМЕЕТЕ ПИСЬМЕННОЕ РАЗРЕШЕНИЕ!

console.log('🛡️ Этичный сканер безопасности веб-форм');
console.log('⚠️  ВНИМАНИЕ: Используйте только с разрешения владельца сайта!');

// Проверка согласия пользователя
function checkEthicalConsent() {
    const consent = confirm(
        '⚠️ ЭТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ ⚠️\n\n' +
        'Этот инструмент предназначен только для тестирования сайтов, которыми вы владеете ' +
        'или на которые у вас есть письменное разрешение владельца.\n\n' +
        'Несанкционированное тестирование чужих сайтов может быть незаконным.\n\n' +
        'Вы подтверждаете, что имеете право тестировать этот сайт?'
    );
    
    if (!consent) {
        console.log('❌ Тестирование отменено пользователем');
        return false;
    }
    
    console.log('✅ Согласие получено. Начинаем этичное тестирование...');
    return true;
}

// Безопасные тестовые payload'ы (не вредоносные)
const testPayloads = {
    // XSS тесты (безопасные)
    xss: [
        '<script>console.log("XSS-Test")</script>',
        '"><script>console.log("XSS")</script>',
        "';console.log('XSS');//",
        '<img src=x onerror=console.log("XSS")>',
        'javascript:console.log("XSS")'
    ],
    
    // SQL инъекции (безопасные)
    sql: [
        "' OR '1'='1",
        '" OR "1"="1',
        "'; SELECT 'test'--",
        "' UNION SELECT 'test'--",
        "admin'--"
    ],
    
    // Command injection (безопасные - только для обнаружения)
    command: [
        '; echo "test"',
        '| echo "test"',
        '&& echo "test"',
        '`echo "test"`',
        '$(echo "test")'
    ],
    
    // Path traversal
    path: [
        '../../../etc/passwd',
        '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts',
        '....//....//....//etc/passwd',
        '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd'
    ],
    
    // CVE-2024-3566 специфичные
    batbad: [
        'package" && echo "CVE-2024-3566-test" && echo "',
        'file.exe" & echo "batbad-test" & echo "',
        'command" | echo "injection-test" | echo "'
    ]
};

// Функция для поиска форм на странице
function findForms() {
    const forms = document.querySelectorAll('form');
    const inputs = document.querySelectorAll('input[type="text"], input[type="search"], textarea');
    
    console.log(`🔍 Найдено форм: ${forms.length}`);
    console.log(`🔍 Найдено текстовых полей: ${inputs.length}`);
    
    return { forms: Array.from(forms), inputs: Array.from(inputs) };
}

// Функция для анализа формы
function analyzeForm(form, index) {
    console.log(`\n📋 Анализ формы ${index + 1}:`);
    console.log(`   Метод: ${form.method || 'GET'}`);
    console.log(`   Действие: ${form.action || 'текущая страница'}`);
    
    const inputs = form.querySelectorAll('input, textarea, select');
    console.log(`   Полей ввода: ${inputs.length}`);
    
    inputs.forEach((input, i) => {
        console.log(`   Поле ${i + 1}: ${input.name || input.id || 'без имени'} (${input.type || input.tagName})`);
    });
    
    return Array.from(inputs);
}

// Функция для безопасного тестирования поля
function testFieldSafely(field, payload, payloadType) {
    // Сохраняем оригинальное значение
    const originalValue = field.value;
    
    try {
        // Устанавливаем тестовое значение
        field.value = payload;
        field.dispatchEvent(new Event('input', { bubbles: true }));
        field.dispatchEvent(new Event('change', { bubbles: true }));
        
        // Проверяем, отразилось ли значение где-то на странице
        const pageContent = document.body.innerHTML;
        const isReflected = pageContent.includes(payload);
        
        if (isReflected) {
            console.warn(`⚠️  Потенциальная уязвимость ${payloadType}: payload отражен на странице`);
            return { vulnerable: true, type: payloadType, payload: payload };
        }
        
        return { vulnerable: false, type: payloadType, payload: payload };
    } finally {
        // Восстанавливаем оригинальное значение
        field.value = originalValue;
        field.dispatchEvent(new Event('input', { bubbles: true }));
        field.dispatchEvent(new Event('change', { bubbles: true }));
    }
}

// Главная функция сканирования
function scanWebsite() {
    if (!checkEthicalConsent()) {
        return;
    }
    
    console.log('\n🚀 Начинаем сканирование...');
    
    const { forms, inputs } = findForms();
    const results = {
        totalForms: forms.length,
        totalInputs: inputs.length,
        vulnerabilities: []
    };
    
    // Анализируем каждую форму
    forms.forEach((form, formIndex) => {
        const formInputs = analyzeForm(form, formIndex);
        
        // Тестируем каждое поле в форме
        formInputs.forEach((field, fieldIndex) => {
            if (field.type === 'password' || field.type === 'hidden') {
                console.log(`   Пропускаем поле ${fieldIndex + 1}: ${field.type}`);
                return;
            }
            
            console.log(`   Тестируем поле ${fieldIndex + 1}...`);
            
            // Тестируем разные типы payload'ов
            Object.entries(testPayloads).forEach(([payloadType, payloads]) => {
                payloads.slice(0, 2).forEach(payload => { // Ограничиваем количество тестов
                    const result = testFieldSafely(field, payload, payloadType);
                    if (result.vulnerable) {
                        results.vulnerabilities.push({
                            formIndex: formIndex,
                            fieldIndex: fieldIndex,
                            fieldName: field.name || field.id || 'unnamed',
                            ...result
                        });
                    }
                });
            });
        });
    });
    
    // Выводим результаты
    console.log('\n📊 РЕЗУЛЬТАТЫ СКАНИРОВАНИЯ:');
    console.log(`   Всего форм: ${results.totalForms}`);
    console.log(`   Всего полей: ${results.totalInputs}`);
    console.log(`   Найдено потенциальных уязвимостей: ${results.vulnerabilities.length}`);
    
    if (results.vulnerabilities.length > 0) {
        console.log('\n🚨 ОБНАРУЖЕННЫЕ УЯЗВИМОСТИ:');
        results.vulnerabilities.forEach((vuln, index) => {
            console.log(`${index + 1}. Форма ${vuln.formIndex + 1}, поле "${vuln.fieldName}"`);
            console.log(`   Тип: ${vuln.type}`);
            console.log(`   Payload: ${vuln.payload}`);
        });
        
        console.log('\n💡 РЕКОМЕНДАЦИИ:');
        console.log('1. Валидируйте и экранируйте все пользовательские данные');
        console.log('2. Используйте параметризованные запросы для SQL');
        console.log('3. Применяйте Content Security Policy (CSP)');
        console.log('4. Экранируйте данные при выводе в HTML');
    } else {
        console.log('\n✅ Явных уязвимостей не обнаружено в базовых тестах');
    }
    
    return results;
}

// Функция для проверки заголовков безопасности
function checkSecurityHeaders() {
    console.log('\n🔒 Проверка заголовков безопасности...');
    
    const securityHeaders = [
        'Content-Security-Policy',
        'X-Frame-Options',
        'X-Content-Type-Options',
        'X-XSS-Protection',
        'Strict-Transport-Security',
        'Referrer-Policy'
    ];
    
    fetch(window.location.href, { method: 'HEAD' })
        .then(response => {
            console.log('\n📋 Заголовки безопасности:');
            
            securityHeaders.forEach(header => {
                const value = response.headers.get(header);
                if (value) {
                    console.log(`✅ ${header}: ${value}`);
                } else {
                    console.log(`❌ ${header}: отсутствует`);
                }
            });
        })
        .catch(error => {
            console.log('❌ Ошибка при проверке заголовков:', error.message);
        });
}

// Функция для анализа cookies
function analyzeCookies() {
    console.log('\n🍪 Анализ cookies...');
    
    const cookies = document.cookie.split(';');
    
    if (cookies.length === 0 || (cookies.length === 1 && cookies[0] === '')) {
        console.log('ℹ️  Cookies не найдены');
        return;
    }
    
    console.log(`Найдено cookies: ${cookies.length}`);
    
    cookies.forEach((cookie, index) => {
        const [name, value] = cookie.trim().split('=');
        console.log(`${index + 1}. ${name}`);
        
        // Проверяем флаги безопасности (упрощенно)
        if (cookie.includes('Secure')) {
            console.log('   ✅ Secure флаг установлен');
        } else {
            console.log('   ⚠️  Secure флаг отсутствует');
        }
        
        if (cookie.includes('HttpOnly')) {
            console.log('   ✅ HttpOnly флаг установлен');
        } else {
            console.log('   ⚠️  HttpOnly флаг отсутствует');
        }
    });
}

// Функция для полного сканирования
function fullSecurityScan() {
    console.log('🛡️ ПОЛНОЕ СКАНИРОВАНИЕ БЕЗОПАСНОСТИ');
    console.log('=====================================');
    
    const results = scanWebsite();
    checkSecurityHeaders();
    analyzeCookies();
    
    console.log('\n📋 ИТОГОВЫЙ ОТЧЕТ:');
    console.log('==================');
    console.log('Сканирование завершено. Проанализируйте результаты выше.');
    console.log('Обязательно сообщите владельцу сайта о найденных проблемах.');
    
    return results;
}

// Экспорт функций
window.SecurityScanner = {
    scanWebsite,
    checkSecurityHeaders,
    analyzeCookies,
    fullSecurityScan,
    findForms
};

console.log('\n📋 ДОСТУПНЫЕ КОМАНДЫ:');
console.log('SecurityScanner.scanWebsite()      - Сканировать формы на уязвимости');
console.log('SecurityScanner.checkSecurityHeaders() - Проверить заголовки безопасности');
console.log('SecurityScanner.analyzeCookies()   - Анализ cookies');
console.log('SecurityScanner.fullSecurityScan() - Полное сканирование');
console.log('SecurityScanner.findForms()        - Найти формы на странице');

console.log('\n💡 Начните с: SecurityScanner.fullSecurityScan()');