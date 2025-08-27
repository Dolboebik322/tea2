import requests
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class TradeConfig:
    """Конфигурация для торговли"""
    api_base_url: str = "https://api.pro.football.fun"
    alchemy_rpc_url: str = "https://base-mainnet.g.alchemy.com/v2/CCDNKip23OyFJ7ssex2-O"
    coinbase_paymaster_url: str = "https://api.developer.coinbase.com/rpc/v1/base/Zvs2anqQIBcBNSP8ftgv2Ce0mQMyEtyI"
    
    # Contract addresses
    smart_wallet_address: str = "0x8f37a8015851976aB75E309100c2511abaBC68AD"
    entry_point_address: str = "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789"
    trade_contract_address: str = "0xba5ed110efdba3d005bfc882d75358acbbb85842"

class FootballTrader:
    def __init__(self, bearer_token: str):
        """
        Инициализация трейдера
        
        Args:
            bearer_token: Bearer токен для авторизации API
        """
        self.config = TradeConfig()
        self.bearer_token = bearer_token
        self.session = requests.Session()
        
        # Заголовки для API запросов
        self.api_headers = {
            "accept": "*/*",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "authorization": f"Bearer {bearer_token}",
            "content-type": "application/json",
            "origin": "https://pro.football.fun",
            "referer": "https://pro.football.fun/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
        }
        
        # Заголовки для RPC запросов
        self.rpc_headers = {
            "accept": "*/*",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/json",
            "origin": "https://pro.football.fun",
            "referer": "https://pro.football.fun/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
        }

    def get_quote(self, player_id: int, shares: int = 1, slippage_bps: int = 500) -> Dict:
        """Получение котировки для покупки игрока"""
        print(f"📤 Получаем котировку для игрока {player_id}...")
        
        payload = {
            "transactionType": "BUY",
            "inputType": "SHARES",
            "oPlayerIds": [player_id],
            "inputValues": [shares],
            "slippageBps": slippage_bps
        }
        
        response = self.session.post(
            f"{self.config.api_base_url}/v1/trade/quote",
            headers=self.api_headers,
            json=payload
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка котировки: {response.status_code}")
            print(f"   Ответ: {response.text}")
            response.raise_for_status()
        
        data = response.json()
        quote_uuid = data["data"]["uuid"]
        total_gold = data["data"]["totalMaxGoldToSpend"]
        
        print(f"✅ Котировка: UUID={quote_uuid}, Gold={total_gold}")
        return data["data"]

    def get_trade_signature(self, quote_uuid: str) -> Dict:
        """Получение подписи для торговли"""
        print("📤 Получаем подпись...")
        
        payload = {"quoteId": quote_uuid}
        
        response = self.session.post(
            f"{self.config.api_base_url}/v1/trade/signature/buy",
            headers=self.api_headers,
            json=payload
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка подписи: {response.status_code}")
            print(f"   Ответ: {response.text}")
            response.raise_for_status()
        
        data = response.json()["data"]
        print(f"✅ Подпись получена: nonce={data['nonce']}, deadline={data['deadline']}")
        return data

    def rpc_call(self, method: str, params: List, rpc_id: int = 1) -> Dict:
        """Выполнение RPC запроса к блокчейну"""
        payload = {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "method": method,
            "params": params
        }
        
        response = self.session.post(
            self.config.alchemy_rpc_url,
            headers=self.rpc_headers,
            json=payload
        )
        
        if response.status_code != 200:
            print(f"❌ RPC ошибка {method}: {response.status_code}")
            response.raise_for_status()
        
        result = response.json()
        if "error" in result:
            print(f"❌ RPC ошибка {method}: {result['error']}")
            return result
        
        return result["result"]

    def build_call_data(self, player_id: int, max_gold_wei: int, signature: str, nonce: int, deadline: int) -> str:
        """Построение callData для смарт-контракта"""
        print("🔧 Строим callData...")
        print(f"   Player ID: {player_id}")
        print(f"   Max Gold Wei: {max_gold_wei} ({hex(max_gold_wei)})")
        print(f"   API Nonce: {nonce}")
        print(f"   Deadline: {deadline} ({hex(deadline)})")
        print(f"   Signature: {signature[:20]}...")
        
        # Функция buyShares(uint256[] calldata playerIds, uint256[] calldata maxGoldAmounts, uint256 nonce, uint256 deadline, bytes calldata signature)
        # Selector: 0x34fcd5be
        
        call_data = "0x34fcd5be"
        
        # Offset для массива playerIds (0x00a0 = 160 bytes)
        call_data += "00000000000000000000000000000000000000000000000000000000000000a0"
        
        # Offset для массива maxGoldAmounts (0x00e0 = 224 bytes)
        call_data += "00000000000000000000000000000000000000000000000000000000000000e0"
        
        # Nonce (32 bytes)
        call_data += f"{nonce:064x}"
        
        # Deadline (32 bytes)
        call_data += f"{deadline:064x}"
        
        # Offset для signature (0x0120 = 288 bytes)
        call_data += "0000000000000000000000000000000000000000000000000000000000000120"
        
        # Массив playerIds
        call_data += "0000000000000000000000000000000000000000000000000000000000000001"
        call_data += f"{player_id:064x}"
        
        # Массив maxGoldAmounts
        call_data += "0000000000000000000000000000000000000000000000000000000000000001"
        call_data += f"{max_gold_wei:064x}"
        
        # Signature
        signature_clean = signature[2:] if signature.startswith('0x') else signature
        signature_length = len(signature_clean) // 2
        
        call_data += f"{signature_length:064x}"
        call_data += signature_clean
        
        # Padding до кратности 32 байт
        padding_needed = (32 - (signature_length % 32)) % 32
        call_data += "00" * padding_needed
        
        print(f"✅ CallData построен: {len(call_data)} символов")
        return call_data

    def validate_user_operation(self, user_op: Dict) -> bool:
        """Валидация UserOperation"""
        required_fields = [
            "sender", "nonce", "initCode", "callData", 
            "callGasLimit", "verificationGasLimit", "preVerificationGas",
            "maxFeePerGas", "maxPriorityFeePerGas", "paymasterAndData", "signature"
        ]
        
        print("🔍 Валидируем UserOperation...")
        for field in required_fields:
            if field not in user_op:
                print(f"❌ Отсутствует поле: {field}")
                return False
            
            value = user_op[field]
            if not isinstance(value, str):
                print(f"❌ Поле {field} должно быть строкой, получено: {type(value)}")
                return False
            
            # Проверяем hex формат для числовых полей
            if field in ["nonce", "callGasLimit", "verificationGasLimit", "preVerificationGas", "maxFeePerGas", "maxPriorityFeePerGas"]:
                if not value.startswith('0x'):
                    print(f"❌ Поле {field} должно начинаться с 0x: {value}")
                    return False
                try:
                    int(value, 16)
                except ValueError:
                    print(f"❌ Поле {field} не является валидным hex: {value}")
                    return False
        
        print("✅ UserOperation валиден")
        return True

    def send_user_operation_direct(self, user_op: Dict) -> Dict:
        """
        Отправка UserOperation напрямую через Alchemy
        """
        print("📤 Отправляем UserOperation через Alchemy...")
        print(f"   Sender: {user_op['sender']}")
        print(f"   Nonce: {user_op['nonce']}")
        print(f"   CallData: {user_op['callData'][:50]}...")
        
        # Валидируем перед отправкой
        if not self.validate_user_operation(user_op):
            return {"error": "Invalid UserOperation format"}
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_sendUserOperation",
            "params": [user_op, self.config.entry_point_address]
        }
        
        print(f"📋 Отправляем payload:")
        print(f"   Method: {payload['method']}")
        print(f"   EntryPoint: {self.config.entry_point_address}")
        print(f"   UserOp keys: {list(user_op.keys())}")
        
        response = self.session.post(
            self.config.alchemy_rpc_url,
            headers=self.rpc_headers,
            json=payload
        )
        
        print(f"📥 Ответ: {response.status_code}")
        
        if response.status_code != 200:
            error_text = response.text
            print(f"❌ Ошибка отправки: {error_text}")
            return {"error": error_text, "status_code": response.status_code}
        
        result = response.json()
        if "error" in result:
            print(f"❌ Ошибка в ответе: {result['error']}")
            print(f"   Код ошибки: {result['error'].get('code')}")
            print(f"   Сообщение: {result['error'].get('message')}")
            return {"error": "Send failed", "details": result}
        
        print(f"✅ UserOperation отправлен: {result['result']}")
        return {"success": True, "userOpHash": result["result"]}

    def buy_player_simple(self, player_id: int, shares: int = 1) -> Dict:
        """
        Упрощенный процесс покупки игрока
        """
        try:
            print(f"🔄 Упрощенная покупка игрока {player_id}...")
            
            # 1. Получаем котировку
            print("\n1️⃣ Получаем котировку...")
            quote_data = self.get_quote(player_id, shares)
            quote_uuid = quote_data["uuid"]
            max_gold_wei = int(quote_data["totalMaxGoldToSpendWei"])
            
            # 2. Получаем подпись
            print("\n2️⃣ Получаем подпись...")
            signature_data = self.get_trade_signature(quote_uuid)
            signature = signature_data["signature"]
            api_nonce = signature_data["nonce"]
            deadline = signature_data["deadline"]
            
            # 3. Получаем базовые данные блокчейна
            print("\n3️⃣ Получаем данные блокчейна...")
            gas_price = self.rpc_call("eth_gasPrice", [])
            priority_fee = self.rpc_call("eth_maxPriorityFeePerGas", [])
            
            # Конвертируем в int и добавляем буфер
            base_fee = int(gas_price, 16)
            priority_fee_int = int(priority_fee, 16)
            max_fee = int(base_fee * 1.2)
            max_priority = int(priority_fee_int * 1.2)
            
            print(f"✅ Газ: base={base_fee}, priority={priority_fee_int}")
            print(f"   Max fee: {max_fee} ({hex(max_fee)})")
            print(f"   Max priority: {max_priority} ({hex(max_priority)})")
            
            # 4. Строим callData
            print("\n4️⃣ Строим callData...")
            call_data = self.build_call_data(
                player_id, max_gold_wei, signature, api_nonce, deadline
            )
            
            # 5. Создаем UserOperation с точными данными из curl
            print("\n5️⃣ Создаем UserOperation...")
            
            # Используем точные данные paymaster из ваших curl запросов
            paymaster_address = "2faeb0760d4230ef2ac21496bb4f0b47d634fd4c"  # Без 0x
            deadline_hex = hex(deadline)[2:].zfill(8)
            
            # Строим paymaster данные точно как в curl запросах
            # Формат: paymaster_address + "000" + deadline + padding
            paymaster_data = f"0x{paymaster_address}000{deadline_hex}0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
            
            user_op = {
                "sender": self.config.smart_wallet_address,
                "nonce": "0x0",  # Nonce 0 как в ваших запросах
                "initCode": "0x",
                "callData": call_data,
                "callGasLimit": "0x39bb8",  # Из curl запросов
                "verificationGasLimit": "0x1b7740",  # Стандартное значение
                "preVerificationGas": "0x6b9f",  # Минимальное значение
                "maxFeePerGas": hex(max_fee),
                "maxPriorityFeePerGas": hex(max_priority),
                "paymasterAndData": paymaster_data,
                "signature": "0x"  # Пустая подпись для AA кошелька
            }
            
            print(f"✅ UserOperation создан:")
            print(f"   Sender: {user_op['sender']}")
            print(f"   Nonce: {user_op['nonce']}")
            print(f"   CallGasLimit: {user_op['callGasLimit']}")
            print(f"   VerificationGasLimit: {user_op['verificationGasLimit']}")
            print(f"   PreVerificationGas: {user_op['preVerificationGas']}")
            print(f"   MaxFeePerGas: {user_op['maxFeePerGas']}")
            print(f"   PaymasterData: {paymaster_data[:50]}...")
            print(f"   PaymasterData length: {len(paymaster_data)}")
            
            # 6. Отправляем UserOperation
            print("\n6️⃣ Отправляем UserOperation...")
            result = self.send_user_operation_direct(user_op)
            
            if "error" in result:
                return {"success": False, "error": result}
            
            print(f"\n✅ Покупка успешна!")
            print(f"   Player ID: {player_id}")
            print(f"   Shares: {shares}")
            print(f"   UserOp Hash: {result['userOpHash']}")
            
            return {
                "success": True,
                "player_id": player_id,
                "shares": shares,
                "quote_uuid": quote_uuid,
                "user_op_hash": result["userOpHash"],
                "max_gold_spent": max_gold_wei
            }
            
        except Exception as e:
            print(f"\n❌ Ошибка: {str(e)}")
            return {"success": False, "error": str(e)}

def main():
    """Главная функция"""
    print("🚀 Football.fun Player Trader v2.1 (Simplified)")
    print("=" * 50)
    
    # Получаем токен от пользователя
    token = input("Введите ваш Bearer токен: ").strip()
    
    if not token:
        print("❌ Токен не может быть пустым!")
        return
    
    # Создаем трейдера
    trader = FootballTrader(token)
    
    # Параметры покупки
    player_id = 246333  # ID игрока
    shares = 1          # Количество акций
    
    try:
        # Выполняем покупку
        result = trader.buy_player_simple(player_id, shares)
        
        if result["success"]:
            print(f"\n🎉 Покупка завершена успешно!")
            print(f"   UserOp Hash: {result['user_op_hash']}")
        else:
            print(f"\n❌ Покупка не удалась: {result['error']}")
            
    except Exception as e:
        print(f"\n❌ Произошла ошибка: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()