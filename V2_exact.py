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
        """Инициализация трейдера"""
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
            response.raise_for_status()
        
        result = response.json()
        if "error" in result:
            print(f"❌ RPC ошибка {method}: {result['error']}")
            return result
        
        return result["result"]

    def build_exact_call_data(self, player_id: int, max_gold_wei: int, signature: str, nonce: int, deadline: int) -> str:
        """
        Построение точного callData на основе curl запросов
        
        Анализ callData из curl:
        0x34fcd5be - selector функции
        Затем идут данные для batched операций (approve + buyShares)
        """
        print("🔧 Строим точный callData на основе curl запросов...")
        
        # Это точный callData из ваших curl запросов, но с обновленными параметрами
        # Структура: batched операция (approve USDC + buyShares)
        
        # Selector для executeBatch
        call_data = "0x34fcd5be"
        
        # Offset для массива targets
        call_data += "0000000000000000000000000000000000000000000000000000000000000020"
        
        # Количество операций (2: approve + buyShares)
        call_data += "0000000000000000000000000000000000000000000000000000000000000002"
        
        # Offset для первого call
        call_data += "0000000000000000000000000000000000000000000000000000000000000040"
        
        # Offset для второго call  
        call_data += "0000000000000000000000000000000000000000000000000000000000000120"
        
        # Первая операция: approve USDC
        # Target: USDC contract
        call_data += "000000000000000000000000833589fcd6edb6e08f4c7c32d4f71b54bda02913"
        call_data += "0000000000000000000000000000000000000000000000000000000000000000"
        call_data += "0000000000000000000000000000000000000000000000000000000000000060"
        
        # Approve calldata length
        call_data += "0000000000000000000000000000000000000000000000000000000000000044"
        
        # approve(spender, amount) - selector: 0x095ea7b3
        call_data += "095ea7b3"
        # Spender: trade contract
        call_data += "0000000000000000000000009da1bb4e725acc0d96010b7ce2a7244cda446617"
        # Amount: max_gold_wei in hex, padded to 32 bytes
        call_data += f"{max_gold_wei:064x}"
        
        # Padding
        call_data += "00000000000000000000000000000000000000000000000000000000"
        
        # Вторая операция: buyShares
        # Target: trade contract
        call_data += "0000000000000000000000009da1bb4e725acc0d96010b7ce2a7244cda446617"
        call_data += "0000000000000000000000000000000000000000000000000000000000000000"
        call_data += "0000000000000000000000000000000000000000000000000000000000000060"
        
        # buyShares calldata length
        call_data += "00000000000000000000000000000000000000000000000000000000000001e4"
        
        # buyShares(playerIds[], maxGoldAmounts[], nonce, deadline, user, signature) - selector: 0xea624851
        call_data += "ea624851"
        
        # Offset для playerIds array
        call_data += "00000000000000000000000000000000000000000000000000000000000000e0"
        
        # Offset для maxGoldAmounts array  
        call_data += "0000000000000000000000000000000000000000000000000000000000000120"
        
        # Nonce
        call_data += f"{nonce:064x}"
        
        # Deadline
        call_data += f"{deadline:064x}"
        
        # User address
        call_data += f"000000000000000000000000{self.config.smart_wallet_address[2:].lower()}"
        
        # Offset для signature
        call_data += "0000000000000000000000000000000000000000000000000000000000000160"
        
        # PlayerIds array length
        call_data += "0000000000000000000000000000000000000000000000000000000000000001"
        
        # Player ID
        call_data += f"{player_id:064x}"
        
        # MaxGoldAmounts array length
        call_data += "0000000000000000000000000000000000000000000000000000000000000001"
        
        # Max gold amount
        call_data += f"{max_gold_wei:064x}"
        
        # Signature length
        signature_clean = signature[2:] if signature.startswith('0x') else signature
        signature_length = len(signature_clean) // 2
        call_data += f"{signature_length:064x}"
        
        # Signature data
        call_data += signature_clean
        
        # Padding
        padding_needed = (32 - (signature_length % 32)) % 32
        call_data += "00" * padding_needed
        
        print(f"✅ CallData построен: {len(call_data)} символов")
        return call_data

    def get_nonce_from_blockchain(self) -> str:
        """Получение nonce из блокчейна через EntryPoint"""
        print("📤 Получаем nonce из EntryPoint...")
        
        # EntryPoint.getNonce(sender, key) где key = 0
        nonce_result = self.rpc_call("eth_call", [{
            "data": f"0x35567e1a000000000000000000000000{self.config.smart_wallet_address[2:].lower()}0000000000000000000000000000000000000000000000000000000000000000",
            "to": self.config.entry_point_address
        }, "latest"])
        
        # Конвертируем в правильный формат - убираем ведущие нули
        if nonce_result and nonce_result != "0x":
            nonce_int = int(nonce_result, 16)
            formatted_nonce = hex(nonce_int) if nonce_int > 0 else "0x0"
        else:
            formatted_nonce = "0x0"
        
        print(f"✅ Blockchain nonce: {nonce_result} -> {formatted_nonce}")
        return formatted_nonce

    def get_paymaster_stub_data(self, user_op: Dict) -> str:
        """Получение stub данных от paymaster"""
        print("📤 Получаем paymaster stub данные...")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "pm_getPaymasterStubData",
            "params": [
                user_op,
                self.config.entry_point_address,
                "0x2105",  # Chain ID для Base в hex
                None
            ]
        }
        
        response = self.session.post(
            self.config.coinbase_paymaster_url,
            headers=self.rpc_headers,
            json=payload
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка paymaster stub: {response.status_code}")
            return "0x"
        
        result = response.json()
        if "error" in result:
            print(f"❌ Ошибка paymaster stub: {result['error']}")
            return "0x"
        
        paymaster_data = result["result"]["paymasterAndData"]
        print(f"✅ Paymaster stub получен: {paymaster_data[:50]}...")
        return paymaster_data

    def send_user_operation(self, user_op: Dict) -> Dict:
        """Отправка UserOperation"""
        print("📤 Отправляем UserOperation...")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "eth_sendUserOperation",
            "params": [user_op, self.config.entry_point_address]
        }
        
        print(f"📋 Payload:")
        print(f"   Method: {payload['method']}")
        print(f"   UserOp keys: {list(user_op.keys())}")
        print(f"   Nonce: {user_op['nonce']}")
        print(f"   CallGasLimit: {user_op['callGasLimit']}")
        print(f"   PaymasterData: {user_op['paymasterAndData'][:50]}...")
        
        response = self.session.post(
            self.config.coinbase_paymaster_url,
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
            print(f"❌ Ошибка в ответе: {result}")
            return {"error": "Send failed", "details": result}
        
        print(f"✅ UserOperation отправлен: {result['result']}")
        return {"success": True, "userOpHash": result["result"]}

    def buy_player_exact(self, player_id: int, shares: int = 1) -> Dict:
        """
        Точная покупка игрока на основе curl запросов
        """
        try:
            print(f"🔄 Точная покупка игрока {player_id} на основе curl данных...")
            
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
            
            # 3. Используем фиксированный nonce как в curl запросах
            print("\n3️⃣ Используем фиксированный nonce...")
            # В реальных curl запросах nonce был: 0x198eb498bc70000000000000000
            # Это специальный формат для Account Abstraction кошельков
            blockchain_nonce = "0x0"  # Используем простой nonce для начала
            print(f"✅ Nonce: {blockchain_nonce}")
            
            # 4. Получаем цены на газ
            print("\n4️⃣ Получаем цены на газ...")
            gas_price = self.rpc_call("eth_gasPrice", [])
            priority_fee = self.rpc_call("eth_maxPriorityFeePerGas", [])
            
            base_fee = int(gas_price, 16)
            priority_fee_int = int(priority_fee, 16)
            max_fee = int(base_fee * 1.2)
            max_priority = int(priority_fee_int * 1.8)  # Увеличиваем приоритет
            
            print(f"✅ Газ: base={base_fee}, priority={priority_fee_int}")
            print(f"   Max fee: {max_fee} ({hex(max_fee)})")
            print(f"   Max priority: {max_priority} ({hex(max_priority)})")
            
            # 5. Строим callData
            print("\n5️⃣ Строим callData...")
            call_data = self.build_exact_call_data(
                player_id, max_gold_wei, signature, api_nonce, deadline
            )
            
            # 6. Создаем базовый UserOperation для получения paymaster данных
            print("\n6️⃣ Создаем базовый UserOperation...")
            
            # Signature как в curl запросах - заглушка для получения paymaster данных
            stub_signature = "0x0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000041fffffffffffffffffffffffffffffff0000000000000000000000000000000007aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa1c00000000000000000000000000000000000000000000000000000000000000"
            
            base_user_op = {
                "sender": self.config.smart_wallet_address,
                "nonce": blockchain_nonce,
                "initCode": "0x",
                "callData": call_data,
                "callGasLimit": "0x0",  # Будет заполнено paymaster'ом
                "verificationGasLimit": "0x0",  # Будет заполнено paymaster'ом
                "preVerificationGas": "0x0",  # Будет заполнено paymaster'ом
                "maxFeePerGas": hex(max_fee),
                "maxPriorityFeePerGas": hex(max_priority),
                "signature": stub_signature
            }
            
            # 7. Используем фиксированные paymaster данные из curl
            print("\n7️⃣ Используем фиксированные paymaster данные...")
            # Из curl запросов
            paymaster_address = "2faeb0760d4230ef2ac21496bb4f0b47d634fd4c"
            deadline_hex = hex(deadline)[2:].zfill(8)
            
            # Точная структура из curl ответа pm_getPaymasterStubData
            paymaster_data = f"0x{paymaster_address}000{deadline_hex}000000000000a583b20c1248462d8ce02d9a0f258b1b010100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006978011259b7582d190d2a939c27656a3e5cb985dc573867ba21a18fa410da495a506e904db886172d336c4140acb7f430a9873af0b9ef00b33361dfea90356362411b"
            
            print(f"✅ Paymaster данные установлены: {paymaster_data[:50]}...")
            
            # 8. Создаем финальный UserOperation с реальными значениями из curl
            print("\n8️⃣ Создаем финальный UserOperation...")
            
            # Реальная подпись из curl запросов
            real_signature = "0x0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000041e16e7eb2993dc27c115a730cd3adaec7f856889bdcc27afaee492201fbe46cd2588a999ec07a75a1222832a123a46eeec37c33903ee53f529fa1496ae836a3201b00000000000000000000000000000000000000000000000000000000000000"
            
            final_user_op = {
                "sender": self.config.smart_wallet_address,
                "nonce": blockchain_nonce,
                "initCode": "0x",
                "callData": call_data,
                "callGasLimit": "0x39bb8",  # Из curl
                "verificationGasLimit": "0x141e9",  # Из curl
                "preVerificationGas": "0xdbbf",  # Из curl
                "maxFeePerGas": hex(max_fee),
                "maxPriorityFeePerGas": hex(max_priority),
                "paymasterAndData": paymaster_data,
                "signature": real_signature
            }
            
            print(f"✅ Финальный UserOperation:")
            print(f"   Nonce: {final_user_op['nonce']}")
            print(f"   CallGasLimit: {final_user_op['callGasLimit']}")
            print(f"   VerificationGasLimit: {final_user_op['verificationGasLimit']}")
            print(f"   PreVerificationGas: {final_user_op['preVerificationGas']}")
            
            # 9. Отправляем UserOperation
            print("\n9️⃣ Отправляем UserOperation...")
            result = self.send_user_operation(final_user_op)
            
            if "error" in result:
                return {"success": False, "error": result}
            
            print(f"\n✅ Покупка успешна!")
            print(f"   Player ID: {player_id}")
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
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

def main():
    """Главная функция"""
    print("🚀 Football.fun Player Trader v2.2 (Exact)")
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
        result = trader.buy_player_exact(player_id, shares)
        
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