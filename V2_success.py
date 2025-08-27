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

    def get_blockchain_nonce(self) -> str:
        """
        Получение правильного nonce для Account Abstraction кошелька
        
        Из успешного curl запроса видно, что nonce имеет формат:
        0x198eb498bc70000000000000000
        
        Это комбинированный nonce для AA кошельков
        """
        print("📤 Получаем nonce для AA кошелька...")
        
        # EntryPoint.getNonce(sender, key) где key = 0
        nonce_result = self.rpc_call("eth_call", [{
            "data": f"0x35567e1a000000000000000000000000{self.config.smart_wallet_address[2:].lower()}0000000000000000000000000000000000000000000000000000000000000000",
            "to": self.config.entry_point_address
        }, "latest"])
        
        if nonce_result and nonce_result != "0x":
            # Для AA кошельков nonce может быть в специальном формате
            nonce_int = int(nonce_result, 16)
            if nonce_int == 0:
                # Если nonce = 0, используем базовый формат
                formatted_nonce = "0x0"
            else:
                # Используем полученный nonce
                formatted_nonce = nonce_result
        else:
            formatted_nonce = "0x0"
        
        print(f"✅ Blockchain nonce: {formatted_nonce}")
        return formatted_nonce

    def build_exact_call_data_from_curl(self, player_id: int, max_gold_wei: int, signature: str, nonce: int, deadline: int) -> str:
        """
        Построение точного callData на основе успешного curl запроса
        
        Из curl видно, что используется batched операция:
        1. approve(USDC, trade_contract, amount)
        2. buyShares(playerIds, maxGoldAmounts, nonce, deadline, user, signature)
        """
        print("🔧 Строим точный callData на основе успешного curl...")
        
        # Используем точный callData из успешного curl, но с нашими параметрами
        # Selector: 0x34fcd5be (executeBatch)
        call_data = "0x34fcd5be"
        
        # Параметры для batched операции
        call_data += "0000000000000000000000000000000000000000000000000000000000000020"  # offset
        call_data += "0000000000000000000000000000000000000000000000000000000000000002"  # count = 2
        call_data += "0000000000000000000000000000000000000000000000000000000000000040"  # offset 1
        call_data += "0000000000000000000000000000000000000000000000000000000000000120"  # offset 2
        
        # Первая операция: approve USDC
        call_data += "000000000000000000000000833589fcd6edb6e08f4c7c32d4f71b54bda02913"  # USDC address
        call_data += "0000000000000000000000000000000000000000000000000000000000000000"  # value = 0
        call_data += "0000000000000000000000000000000000000000000000000000000000000060"  # data offset
        call_data += "0000000000000000000000000000000000000000000000000000000000000044"  # data length
        
        # approve(spender, amount)
        call_data += "095ea7b3"  # approve selector
        call_data += "0000000000000000000000009da1bb4e725acc0d96010b7ce2a7244cda446617"  # trade contract
        call_data += f"{max_gold_wei:064x}"  # amount
        call_data += "00000000000000000000000000000000000000000000000000000000"  # padding
        
        # Вторая операция: buyShares
        call_data += "0000000000000000000000009da1bb4e725acc0d96010b7ce2a7244cda446617"  # trade contract
        call_data += "0000000000000000000000000000000000000000000000000000000000000000"  # value = 0
        call_data += "0000000000000000000000000000000000000000000000000000000000000060"  # data offset
        call_data += "00000000000000000000000000000000000000000000000000000000000001e4"  # data length
        
        # buyShares function call
        call_data += "ea624851"  # buyShares selector
        call_data += "00000000000000000000000000000000000000000000000000000000000000e0"  # playerIds offset
        call_data += "0000000000000000000000000000000000000000000000000000000000000120"  # maxGoldAmounts offset
        call_data += f"{nonce:064x}"  # nonce
        call_data += f"{deadline:064x}"  # deadline
        call_data += f"000000000000000000000000{self.config.smart_wallet_address[2:].lower()}"  # user
        call_data += "0000000000000000000000000000000000000000000000000000000000000160"  # signature offset
        
        # PlayerIds array
        call_data += "0000000000000000000000000000000000000000000000000000000000000001"  # length
        call_data += f"{player_id:064x}"  # player ID
        
        # MaxGoldAmounts array
        call_data += "0000000000000000000000000000000000000000000000000000000000000001"  # length
        call_data += f"{max_gold_wei:064x}"  # max gold amount
        
        # Signature
        signature_clean = signature[2:] if signature.startswith('0x') else signature
        signature_length = len(signature_clean) // 2
        call_data += f"{signature_length:064x}"  # signature length
        call_data += signature_clean  # signature data
        
        # Padding
        padding_needed = (32 - (signature_length % 32)) % 32
        call_data += "00" * padding_needed
        
        print(f"✅ CallData построен: {len(call_data)} символов")
        return call_data

    def send_user_operation(self, user_op: Dict) -> Dict:
        """Отправка UserOperation через Coinbase paymaster"""
        print("📤 Отправляем UserOperation...")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 9,  # Используем тот же ID как в успешном curl
            "method": "eth_sendUserOperation",
            "params": [user_op, self.config.entry_point_address]
        }
        
        print(f"📋 Payload:")
        print(f"   Method: {payload['method']}")
        print(f"   Sender: {user_op['sender']}")
        print(f"   Nonce: {user_op['nonce']}")
        print(f"   CallGasLimit: {user_op['callGasLimit']}")
        print(f"   VerificationGasLimit: {user_op['verificationGasLimit']}")
        print(f"   PreVerificationGas: {user_op['preVerificationGas']}")
        print(f"   MaxFeePerGas: {user_op['maxFeePerGas']}")
        print(f"   MaxPriorityFeePerGas: {user_op['maxPriorityFeePerGas']}")
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
        
        user_op_hash = result["result"]
        print(f"✅ UserOperation отправлен!")
        print(f"   UserOp Hash: {user_op_hash}")
        return {"success": True, "userOpHash": user_op_hash}

    def buy_player_success(self, player_id: int, shares: int = 1) -> Dict:
        """
        Покупка игрока на основе успешного curl запроса
        """
        try:
            print(f"🔄 Покупка игрока {player_id} на основе успешного curl...")
            
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
            
            # 3. Получаем nonce
            print("\n3️⃣ Получаем nonce...")
            blockchain_nonce = self.get_blockchain_nonce()
            
            # 4. Получаем цены на газ
            print("\n4️⃣ Получаем цены на газ...")
            gas_price = self.rpc_call("eth_gasPrice", [])
            priority_fee = self.rpc_call("eth_maxPriorityFeePerGas", [])
            
            base_fee = int(gas_price, 16)
            priority_fee_int = int(priority_fee, 16)
            
            # Используем более высокие значения для надежности
            max_fee = int(base_fee * 1.5)
            max_priority = int(priority_fee_int * 1.8)
            
            print(f"✅ Газ: base={base_fee}, priority={priority_fee_int}")
            print(f"   Max fee: {max_fee} ({hex(max_fee)})")
            print(f"   Max priority: {max_priority} ({hex(max_priority)})")
            
            # 5. Строим callData
            print("\n5️⃣ Строим callData...")
            call_data = self.build_exact_call_data_from_curl(
                player_id, max_gold_wei, signature, api_nonce, deadline
            )
            
            # 6. Создаем paymaster данные на основе успешного curl
            print("\n6️⃣ Создаем paymaster данные...")
            paymaster_address = "2faeb0760d4230ef2ac21496bb4f0b47d634fd4c"
            deadline_hex = hex(deadline)[2:].zfill(8)
            
            # Точные paymaster данные из успешного curl
            paymaster_data = f"0x{paymaster_address}000{deadline_hex}000000000000a583b20c1248462d8ce02d9a0f258b1b0001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000069788b9da7166635d877fa3d86a9d156157b215633cb1eef404f900b5bf2c53367ad10ff3b8dd81d5ca32cefd3e1eb843a9404d89bde4950e9a96950fc7910ca9a0a1b"
            
            print(f"✅ Paymaster данные: {paymaster_data[:50]}...")
            
            # 7. Создаем UserOperation точно как в успешном curl
            print("\n7️⃣ Создаем UserOperation...")
            
            # Точная подпись из успешного curl
            signature_exact = "0x0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000041e16e7eb2993dc27c115a730cd3adaec7f856889bdcc27afaee492201fbe46cd2588a999ec07a75a1222832a123a46eeec37c33903ee53f529fa1496ae836a3201b00000000000000000000000000000000000000000000000000000000000000"
            
            user_op = {
                "callData": call_data,
                "callGasLimit": "0x39bb8",  # Из успешного curl
                "initCode": "0x",
                "maxFeePerGas": hex(max_fee),
                "maxPriorityFeePerGas": hex(max_priority),
                "nonce": blockchain_nonce,
                "paymasterAndData": paymaster_data,
                "preVerificationGas": "0xdbbf",  # Из успешного curl
                "sender": self.config.smart_wallet_address,
                "signature": signature_exact,
                "verificationGasLimit": "0x141e9"  # Из успешного curl
            }
            
            print(f"✅ UserOperation создан")
            
            # 8. Отправляем UserOperation
            print("\n8️⃣ Отправляем UserOperation...")
            result = self.send_user_operation(user_op)
            
            if "error" in result:
                return {"success": False, "error": result}
            
            print(f"\n🎉 Покупка успешна!")
            print(f"   Player ID: {player_id}")
            print(f"   Shares: {shares}")
            print(f"   UserOp Hash: {result['userOpHash']}")
            print(f"   Max Gold Spent: {max_gold_wei}")
            
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
    print("🚀 Football.fun Player Trader v2.3 (Success Based)")
    print("=" * 55)
    
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
        result = trader.buy_player_success(player_id, shares)
        
        if result["success"]:
            print(f"\n🎉 Покупка завершена успешно!")
            print(f"   UserOp Hash: {result['user_op_hash']}")
            print(f"   Вы можете проверить транзакцию на: https://basescan.org/tx/{result['user_op_hash']}")
        else:
            print(f"\n❌ Покупка не удалась: {result['error']}")
            
    except Exception as e:
        print(f"\n❌ Произошла ошибка: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()