#!/usr/bin/env python3
"""
ABI Decoder - Утилита для расшифровки data поля в eth_call
"""

import json
from typing import Dict, List, Any

class ABIDecoder:
    
    # Известные function selectors
    FUNCTION_SELECTORS = {
        "0x250b1b41": {
            "name": "unknown_function_1",
            "signature": "unknown()",
            "inputs": []
        },
        "0x35567e1a": {
            "name": "getNonce",
            "signature": "getNonce(address,uint192)",
            "inputs": [
                {"name": "sender", "type": "address"},
                {"name": "key", "type": "uint192"}
            ]
        },
        "0x34fcd5be": {
            "name": "executeBatch",
            "signature": "executeBatch(bytes32,bytes)",
            "inputs": [
                {"name": "mode", "type": "bytes32"},
                {"name": "executionCalldata", "type": "bytes"}
            ]
        },
        "0x095ea7b3": {
            "name": "approve",
            "signature": "approve(address,uint256)",
            "inputs": [
                {"name": "spender", "type": "address"},
                {"name": "amount", "type": "uint256"}
            ]
        },
        "0x1e4ea624": {
            "name": "buyShares",
            "signature": "buyShares(uint256[],uint256[],uint256,uint256,address,bytes)",
            "inputs": [
                {"name": "playerIds", "type": "uint256[]"},
                {"name": "maxGoldAmounts", "type": "uint256[]"},
                {"name": "maxGoldToSpend", "type": "uint256"},
                {"name": "deadline", "type": "uint256"},
                {"name": "user", "type": "address"},
                {"name": "signature", "type": "bytes"}
            ]
        }
    }
    
    def decode_data(self, data: str) -> Dict[str, Any]:
        """Основная функция декодирования"""
        if not data.startswith("0x"):
            data = "0x" + data
        
        if len(data) < 10:  # Минимум 0x + 4 байта selector
            return {"error": "Data too short"}
        
        # Извлекаем function selector
        selector = data[:10]  # 0x + 8 hex chars = 4 bytes
        params_data = data[10:]  # Остальные данные
        
        result = {
            "selector": selector,
            "raw_data": data,
            "params_hex": params_data
        }
        
        # Ищем известную функцию
        if selector in self.FUNCTION_SELECTORS:
            func_info = self.FUNCTION_SELECTORS[selector]
            result.update({
                "function_name": func_info["name"],
                "function_signature": func_info["signature"],
                "inputs": func_info["inputs"]
            })
            
            # Декодируем параметры
            if func_info["inputs"]:
                result["decoded_params"] = self.decode_parameters(
                    params_data, func_info["inputs"]
                )
        else:
            result["function_name"] = "unknown"
            result["note"] = f"Unknown function selector: {selector}"
        
        return result
    
    def decode_parameters(self, params_hex: str, inputs: List[Dict]) -> Dict[str, Any]:
        """Декодирование параметров функции"""
        if not params_hex:
            return {}
        
        # Простая реализация для базовых типов
        decoded = {}
        offset = 0
        
        for i, input_info in enumerate(inputs):
            param_name = input_info["name"]
            param_type = input_info["type"]
            
            if param_type == "address":
                # Address = 20 bytes, но в ABI занимает 32 байта (64 hex chars)
                if offset + 64 <= len(params_hex):
                    address_hex = params_hex[offset:offset+64]
                    # Берем последние 40 символов (20 bytes)
                    address = "0x" + address_hex[-40:]
                    decoded[param_name] = address
                    offset += 64
                    
            elif param_type.startswith("uint"):
                # Uint занимает 32 байта (64 hex chars)
                if offset + 64 <= len(params_hex):
                    uint_hex = params_hex[offset:offset+64]
                    uint_value = int(uint_hex, 16)
                    decoded[param_name] = {
                        "hex": "0x" + uint_hex,
                        "decimal": uint_value
                    }
                    offset += 64
                    
            elif param_type == "bytes32":
                # Bytes32 = 32 байта (64 hex chars)
                if offset + 64 <= len(params_hex):
                    bytes32_hex = params_hex[offset:offset+64]
                    decoded[param_name] = "0x" + bytes32_hex
                    offset += 64
                    
            else:
                # Для сложных типов просто показываем raw данные
                decoded[param_name] = f"<{param_type}> - не реализовано"
        
        return decoded
    
    def analyze_calldata_structure(self, data: str) -> Dict[str, Any]:
        """Анализ структуры calldata"""
        if not data.startswith("0x"):
            data = "0x" + data
        
        analysis = {
            "total_length": len(data),
            "data_length_bytes": (len(data) - 2) // 2,
            "selector": data[:10] if len(data) >= 10 else "N/A",
            "params_length": len(data) - 10 if len(data) >= 10 else 0
        }
        
        # Разбиваем на 32-байтовые блоки для анализа
        if len(data) > 10:
            params = data[10:]
            blocks = []
            for i in range(0, len(params), 64):
                block = params[i:i+64]
                if len(block) == 64:
                    blocks.append({
                        "index": i // 64,
                        "hex": block,
                        "as_uint": int(block, 16),
                        "as_address": "0x" + block[-40:] if block.startswith("000000000000000000000000") else None
                    })
            analysis["parameter_blocks"] = blocks
        
        return analysis

def decode_examples():
    """Декодирование примеров из curl запросов"""
    decoder = ABIDecoder()
    
    examples = [
        {
            "name": "Example 1 - Unknown function",
            "data": "0x250b1b4100000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000020000000000000000000000000d5e5D9099be10ADEf065E45b6444CA4a94fB6367"
        },
        {
            "name": "Example 2 - getNonce",
            "data": "0x35567e1a0000000000000000000000008f37a8015851976ab75e309100c2511ababc68ad00000000000000000000000000000000000000000000000000000198eba23566"
        },
        {
            "name": "Example 3 - executeBatch (partial)",
            "data": "0x34fcd5be0000000000000000000000000000000000000000000000000000000000000020"
        }
    ]
    
    for example in examples:
        print(f"\n{'='*60}")
        print(f"🔍 {example['name']}")
        print(f"{'='*60}")
        
        # Основное декодирование
        result = decoder.decode_data(example['data'])
        print(f"📋 Основная информация:")
        print(f"   Function: {result.get('function_name', 'unknown')}")
        print(f"   Signature: {result.get('function_signature', 'N/A')}")
        print(f"   Selector: {result['selector']}")
        
        if 'decoded_params' in result:
            print(f"\n📝 Декодированные параметры:")
            for param_name, param_value in result['decoded_params'].items():
                print(f"   {param_name}: {param_value}")
        
        # Структурный анализ
        print(f"\n🔬 Структурный анализ:")
        analysis = decoder.analyze_calldata_structure(example['data'])
        print(f"   Общая длина: {analysis['total_length']} символов")
        print(f"   Данных: {analysis['data_length_bytes']} байт")
        print(f"   Параметров: {analysis['params_length']} символов")
        
        if 'parameter_blocks' in analysis:
            print(f"\n📊 32-байтовые блоки:")
            for block in analysis['parameter_blocks'][:5]:  # Показываем первые 5
                print(f"   Блок {block['index']}: {block['hex']}")
                print(f"     Как uint: {block['as_uint']}")
                if block['as_address']:
                    print(f"     Как address: {block['as_address']}")

def interactive_decoder():
    """Интерактивный декодер"""
    decoder = ABIDecoder()
    
    print("🔍 Интерактивный ABI декодер")
    print("Введите 'quit' для выхода")
    print("-" * 40)
    
    while True:
        data = input("\nВведите data (hex): ").strip()
        
        if data.lower() in ['quit', 'exit', 'q']:
            break
        
        if not data:
            continue
        
        try:
            result = decoder.decode_data(data)
            
            print(f"\n📋 Результат декодирования:")
            print(f"   Function: {result.get('function_name', 'unknown')}")
            print(f"   Selector: {result['selector']}")
            
            if 'function_signature' in result:
                print(f"   Signature: {result['function_signature']}")
            
            if 'decoded_params' in result:
                print(f"   Параметры:")
                for name, value in result['decoded_params'].items():
                    print(f"     {name}: {value}")
            
            if result.get('function_name') == 'unknown':
                print(f"   Note: {result.get('note', 'Unknown function')}")
                
        except Exception as e:
            print(f"❌ Ошибка декодирования: {e}")

if __name__ == "__main__":
    print("🚀 ABI Decoder v1.0")
    print("="*50)
    
    # Показываем примеры
    decode_examples()
    
    # Запускаем интерактивный режим
    print(f"\n{'='*60}")
    interactive_decoder()
    
    print("\n👋 До свидания!")