#!/usr/bin/env python3
"""
Быстрое декодирование data поля из eth_call
"""

def quick_decode(data: str):
    """Быстрое декодирование calldata"""
    if not data.startswith("0x"):
        data = "0x" + data
    
    print(f"🔍 Анализ calldata: {data[:50]}...")
    print(f"   Общая длина: {len(data)} символов ({(len(data)-2)//2} байт)")
    
    if len(data) < 10:
        print("❌ Слишком короткие данные")
        return
    
    # Function selector (первые 4 байта)
    selector = data[:10]
    params = data[10:]
    
    print(f"   Function selector: {selector}")
    
    # Известные селекторы
    selectors = {
        "0x250b1b41": "unknown_function_1",
        "0x35567e1a": "getNonce(address,uint192)",
        "0x34fcd5be": "executeBatch(bytes32,bytes)", 
        "0x095ea7b3": "approve(address,uint256)",
        "0x1e4ea624": "buyShares(...)"
    }
    
    if selector in selectors:
        print(f"   Function: {selectors[selector]}")
    else:
        print(f"   Function: UNKNOWN")
    
    # Разбиваем параметры на 32-байтовые блоки
    if params:
        print(f"   Параметры ({len(params)} символов):")
        
        for i in range(0, len(params), 64):
            block = params[i:i+64]
            if len(block) == 64:
                block_num = i // 64
                uint_val = int(block, 16)
                
                print(f"     Блок {block_num}: {block}")
                print(f"       Как uint: {uint_val}")
                
                # Если похоже на адрес (начинается с нулей)
                if block.startswith("000000000000000000000000"):
                    address = "0x" + block[-40:]
                    print(f"       Как address: {address}")
                
                # Если небольшое число, показываем в разных форматах
                if uint_val < 10**10:
                    print(f"       Как timestamp: {uint_val}")
                
                print()

# Примеры из ваших curl запросов
examples = [
    "0x250b1b4100000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000020000000000000000000000000d5e5D9099be10ADEf065E45b6444CA4a94fB6367",
    "0x35567e1a0000000000000000000000008f37a8015851976ab75e309100c2511ababc68ad00000000000000000000000000000000000000000000000000000198eba23566"
]

if __name__ == "__main__":
    print("🚀 Quick ABI Decoder")
    print("="*50)
    
    for i, example in enumerate(examples, 1):
        print(f"\n📝 Пример {i}:")
        quick_decode(example)
        print("-" * 50)
    
    # Интерактивный режим
    print("\n🔧 Интерактивный режим (введите 'q' для выхода):")
    while True:
        data = input("\nВведите calldata: ").strip()
        if data.lower() in ['q', 'quit', 'exit']:
            break
        if data:
            quick_decode(data)
            print("-" * 30)