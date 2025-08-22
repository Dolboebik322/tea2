// CVE-2024-3566 - Безопасные примеры для консоли браузера
// Эти функции можно копировать и выполнять в консоли браузера

console.log('🛡️ CVE-2024-3566 (BatBadBut) - Безопасные примеры для браузера');
console.log('Скопируйте и выполните любую из функций ниже:');

// Функция валидации входных данных
function validateUserInput(input) {
    console.log(`\n🔍 Проверка ввода: "${input}"`);
    
    // Проверка на опасные символы
    const dangerousChars = /[&|;`$(){}[\]<>]/;
    const hasQuotes = /["']/;
    const hasShellOperators = /(\|\||&&|;|`)/;
    
    let issues = [];
    let safe = true;

    if (dangerousChars.test(input)) {
        const found = input.match(dangerousChars);
        issues.push(`❌ Опасные символы: ${found.join(', ')}`);
        safe = false;
    }

    if (hasQuotes.test(input)) {
        issues.push('⚠️  Кавычки обнаружены - возможна инъекция');
        safe = false;
    }

    if (hasShellOperators.test(input)) {
        issues.push('🚨 Shell операторы - высокий риск!');
        safe = false;
    }

    if (safe) {
        console.log('✅ Ввод выглядит безопасным');
    } else {
        console.log('🚫 ПРОБЛЕМЫ БЕЗОПАСНОСТИ:');
        issues.forEach(issue => console.log(`   ${issue}`));
    }
    
    return safe;
}

// Функция демонстрации экранирования
function demonstrateEscaping(input) {
    console.log(`\n📝 Демонстрация экранирования для: "${input}"`);
    
    // Windows CMD экранирование
    const windowsEscaped = '"' + input.replace(/"/g, '""') + '"';
    console.log(`Windows CMD: ${windowsEscaped}`);
    
    // Unix shell экранирование (упрощенный)
    const unixEscaped = "'" + input.replace(/'/g, "'\"'\"'") + "'";
    console.log(`Unix shell: ${unixEscaped}`);
    
    // Показать разницу
    console.log(`Исходная длина: ${input.length}`);
    console.log(`После экранирования: ${windowsEscaped.length}`);
    
    return {
        original: input,
        windows: windowsEscaped,
        unix: unixEscaped
    };
}

// Функция для анализа payload'ов
function analyzePayload(payload) {
    console.log(`\n🔬 Анализ payload: "${payload}"`);
    
    const patterns = {
        'Command injection': /(\|\||&&|;)/,
        'Quote escaping': /["']/,
        'File operations': /(rm|del|copy|move)/i,
        'System commands': /(calc|cmd|bash|sh|whoami)/i,
        'Redirection': /[<>]/
    };
    
    let threats = [];
    
    Object.entries(patterns).forEach(([threat, pattern]) => {
        if (pattern.test(payload)) {
            const matches = payload.match(pattern);
            threats.push({
                type: threat,
                matches: matches
            });
        }
    });
    
    if (threats.length === 0) {
        console.log('✅ Угроз не обнаружено');
    } else {
        console.log('🚨 Обнаруженные угрозы:');
        threats.forEach(threat => {
            console.log(`   ${threat.type}: ${threat.matches.join(', ')}`);
        });
    }
    
    return threats;
}

// Функция для демонстрации безопасных практик
function showSafePractices() {
    console.log('\n🛡️ БЕЗОПАСНЫЕ ПРАКТИКИ:');
    console.log('1. Всегда валидируйте пользовательский ввод');
    console.log('2. Используйте белые списки допустимых символов');
    console.log('3. Экранируйте специальные символы');
    console.log('4. Никогда не выполняйте команды с shell=true');
    console.log('5. Используйте абсолютные пути к исполняемым файлам');
    console.log('6. Указывайте расширения .exe на Windows');
}

// Функция тестирования различных payload'ов
function testCommonPayloads() {
    console.log('\n🧪 Тестирование обычных payload\'ов:');
    
    const payloads = [
        'normal-package',
        'package" && calc.exe && echo "',
        'https://repo.git" && whoami && echo "',
        '--help; rm -rf /',
        'test`whoami`test',
        'file.txt > output.txt'
    ];
    
    payloads.forEach((payload, index) => {
        console.log(`\n--- Тест ${index + 1} ---`);
        const safe = validateUserInput(payload);
        if (!safe) {
            analyzePayload(payload);
        }
    });
}

// Интерактивные примеры для копирования
console.log('\n📋 ПРИМЕРЫ ДЛЯ КОПИРОВАНИЯ:');
console.log('validateUserInput("normal-package")');
console.log('validateUserInput("package\\" && calc.exe && echo \\"")');
console.log('demonstrateEscaping("test\\"dangerous\\"input")');
console.log('analyzePayload("cmd && whoami")');
console.log('testCommonPayloads()');
console.log('showSafePractices()');

console.log('\n💡 Скопируйте любую строку выше и выполните в консоли!');

// Экспорт функций для использования
if (typeof window !== 'undefined') {
    window.CVEDemo = {
        validateUserInput,
        demonstrateEscaping,
        analyzePayload,
        testCommonPayloads,
        showSafePractices
    };
    console.log('\n🌐 Функции доступны через window.CVEDemo');
}