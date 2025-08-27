import requests
import json
from typing import Dict

class FootballTrader:
    def __init__(self, bearer_token: str):
        """Инициализация трейдера"""
        self.bearer_token = bearer_token
        self.session = requests.Session()
        
        # Точные заголовки из curl
        self.api_headers = {
            "accept": "*/*",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "authorization": f"Bearer {bearer_token}",
            "content-type": "application/json",
            "origin": "https://pro.football.fun",
            "referer": "https://pro.football.fun/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
        }
        
        self.rpc_headers = {
            "accept": "*/*",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/json",
            "origin": "https://pro.football.fun",
            "priority": "u=1, i",
            "referer": "https://pro.football.fun/",
            "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
        }

    def get_quote(self, player_id: int, shares: int = 1) -> Dict:
        """Получение котировки"""
        print(f"📤 Получаем котировку для игрока {player_id}...")
        
        payload = {
            "transactionType": "BUY",
            "inputType": "SHARES",
            "oPlayerIds": [player_id],
            "inputValues": [shares],
            "slippageBps": 500
        }
        
        response = self.session.post(
            "https://api.pro.football.fun/v1/trade/quote",
            headers=self.api_headers,
            json=payload
        )
        
        if response.status_code != 200:
            response.raise_for_status()
        
        data = response.json()["data"]
        print(f"✅ Котировка: UUID={data['uuid']}, Gold={data['totalMaxGoldToSpend']}")
        return data

    def get_signature(self, quote_uuid: str) -> Dict:
        """Получение подписи"""
        print("📤 Получаем подпись...")
        
        response = self.session.post(
            "https://api.pro.football.fun/v1/trade/signature/buy",
            headers=self.api_headers,
            json={"quoteId": quote_uuid}
        )
        
        if response.status_code != 200:
            response.raise_for_status()
        
        data = response.json()["data"]
        print(f"✅ Подпись: nonce={data['nonce']}, deadline={data['deadline']}")
        return data

    def build_calldata(self, player_id: int, max_gold_wei: int, signature: str, nonce: int, deadline: int) -> str:
        """Построение callData"""
        print("🔧 Строим callData...")
        
        calldata = "0x34fcd5be"
        calldata += "0000000000000000000000000000000000000000000000000000000000000020"
        calldata += "0000000000000000000000000000000000000000000000000000000000000002"
        calldata += "0000000000000000000000000000000000000000000000000000000000000040"
        calldata += "0000000000000000000000000000000000000000000000000000000000000120"
        
        # Approve USDC
        calldata += "000000000000000000000000833589fcd6edb6e08f4c7c32d4f71b54bda02913"
        calldata += "0000000000000000000000000000000000000000000000000000000000000000"
        calldata += "0000000000000000000000000000000000000000000000000000000000000060"
        calldata += "0000000000000000000000000000000000000000000000000000000000000044"
        calldata += "095ea7b3"
        calldata += "0000000000000000000000009da1bb4e725acc0d96010b7ce2a7244cda446617"
        calldata += f"{max_gold_wei:064x}"
        calldata += "00000000000000000000000000000000000000000000000000000000"
        
        # BuyShares
        calldata += "0000000000000000000000009da1bb4e725acc0d96010b7ce2a7244cda446617"
        calldata += "0000000000000000000000000000000000000000000000000000000000000000"
        calldata += "0000000000000000000000000000000000000000000000000000000000000060"
        calldata += "00000000000000000000000000000000000000000000000000000000000001e4"
        calldata += "ea624851"
        calldata += "00000000000000000000000000000000000000000000000000000000000000e0"
        calldata += "0000000000000000000000000000000000000000000000000000000000000120"
        calldata += f"{nonce:064x}"
        calldata += f"{deadline:064x}"
        calldata += "0000000000000000000000008f37a8015851976ab75e309100c2511ababc68ad"
        calldata += "0000000000000000000000000000000000000000000000000000000000000160"
        calldata += "0000000000000000000000000000000000000000000000000000000000000001"
        calldata += f"{player_id:064x}"
        calldata += "0000000000000000000000000000000000000000000000000000000000000001"
        calldata += f"{max_gold_wei:064x}"
        
        # Signature
        signature_clean = signature[2:] if signature.startswith('0x') else signature
        signature_length = len(signature_clean) // 2
        calldata += f"{signature_length:064x}"
        calldata += signature_clean
        
        # Padding
        padding_needed = (32 - (signature_length % 32)) % 32
        calldata += "00" * padding_needed
        
        print(f"✅ CallData построен: {len(calldata)} символов")
        return calldata

    def get_paymaster_data(self, calldata: str, deadline: int) -> str:
        """Получение актуальных paymaster данных"""
        print("📤 Получаем paymaster данные...")
        
        # Базовый UserOperation для получения paymaster данных
        user_op = {
            "callData": calldata,
            "initCode": "0x",
            "maxFeePerGas": "0x22fac23",
            "maxPriorityFeePerGas": "0x1ab3f0",
            "nonce": "0x198eb498bc70000000000000000",  # Правильный nonce из вашего curl
            "sender": "0x8f37a8015851976aB75E309100c2511abaBC68AD",
            "signature": "0x0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000041fffffffffffffffffffffffffffffff0000000000000000000000000000000007aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa1c00000000000000000000000000000000000000000000000000000000000000",
            "callGasLimit": "0x0",
            "verificationGasLimit": "0x0",
            "preVerificationGas": "0x0"
        }
        
        payload = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "pm_getPaymasterStubData",
            "params": [
                user_op,
                "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789",
                "0x2105",
                None
            ]
        }
        
        response = self.session.post(
            "https://api.developer.coinbase.com/rpc/v1/base/Zvs2anqQIBcBNSP8ftgv2Ce0mQMyEtyI",
            headers=self.rpc_headers,
            json=payload
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка paymaster: {response.status_code}")
            return None
        
        result = response.json()
        if "error" in result:
            print(f"❌ Ошибка paymaster: {result['error']}")
            return None
        
        paymaster_data = result["result"]["paymasterAndData"]
        print(f"✅ Paymaster данные получены: {paymaster_data[:50]}...")
        return paymaster_data

    def send_transaction(self, calldata: str, paymaster_data: str) -> Dict:
        """Отправка транзакции"""
        print("📤 Отправляем транзакцию...")
        
        # Финальный UserOperation с правильными данными
        user_op = {
            "callData": calldata,
            "callGasLimit": "0x39bb8",
            "initCode": "0x",
            "maxFeePerGas": "0x22fac23",
            "maxPriorityFeePerGas": "0x1ab3f0",
            "nonce": "0x198eb498bc70000000000000000",  # Правильный nonce
            "paymasterAndData": paymaster_data,
            "preVerificationGas": "0xdbbf",
            "sender": "0x8f37a8015851976aB75E309100c2511abaBC68AD",
            "signature": "0x0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000041e16e7eb2993dc27c115a730cd3adaec7f856889bdcc27afaee492201fbe46cd2588a999ec07a75a1222832a123a46eeec37c33903ee53f529fa1496ae836a3201b00000000000000000000000000000000000000000000000000000000000000",
            "verificationGasLimit": "0x141e9"
        }
        
        payload = {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "eth_sendUserOperation",
            "params": [
                user_op,
                "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789"
            ]
        }
        
        print(f"📋 Отправляем UserOperation:")
        print(f"   Nonce: {user_op['nonce']}")
        print(f"   CallGasLimit: {user_op['callGasLimit']}")
        print(f"   PaymasterData: {paymaster_data[:50]}...")
        
        response = self.session.post(
            "https://api.developer.coinbase.com/rpc/v1/base/Zvs2anqQIBcBNSP8ftgv2Ce0mQMyEtyI",
            headers=self.rpc_headers,
            json=payload
        )
        
        print(f"📥 Ответ: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ HTTP ошибка: {response.text}")
            return {"error": f"HTTP {response.status_code}: {response.text}"}
        
        result = response.json()
        
        if "error" in result:
            print(f"❌ RPC ошибка: {result['error']}")
            return {"error": result["error"]}
        
        user_op_hash = result["result"]
        print(f"✅ Успех! UserOp Hash: {user_op_hash}")
        return {"success": True, "hash": user_op_hash}

    def buy_player(self, player_id: int, shares: int = 1) -> Dict:
        """Полный процесс покупки игрока"""
        try:
            print(f"🔄 Покупка игрока {player_id} (двухэтапный процесс)...")
            
            # 1. Котировка
            print("\n1️⃣ Получаем котировку...")
            quote_data = self.get_quote(player_id, shares)
            max_gold_wei = int(quote_data["totalMaxGoldToSpendWei"])
            
            # 2. Подпись
            print("\n2️⃣ Получаем подпись...")
            signature_data = self.get_signature(quote_data["uuid"])
            signature = signature_data["signature"]
            nonce = signature_data["nonce"]
            deadline = signature_data["deadline"]
            
            # 3. Строим callData
            print("\n3️⃣ Строим callData...")
            calldata = self.build_calldata(player_id, max_gold_wei, signature, nonce, deadline)
            
            # 4. Получаем paymaster данные
            print("\n4️⃣ Получаем paymaster данные...")
            paymaster_data = self.get_paymaster_data(calldata, deadline)
            
            if not paymaster_data:
                return {"success": False, "error": "Не удалось получить paymaster данные"}
            
            # 5. Отправляем транзакцию
            print("\n5️⃣ Отправляем транзакцию...")
            result = self.send_transaction(calldata, paymaster_data)
            
            if "error" in result:
                return {"success": False, "error": result["error"]}
            
            print(f"\n🎉 Покупка успешна!")
            print(f"   Player ID: {player_id}")
            print(f"   Shares: {shares}")
            print(f"   UserOp Hash: {result['hash']}")
            print(f"   Basescan: https://basescan.org/tx/{result['hash']}")
            
            return {
                "success": True,
                "player_id": player_id,
                "shares": shares,
                "hash": result["hash"],
                "max_gold_spent": max_gold_wei
            }
            
        except Exception as e:
            print(f"\n❌ Ошибка: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

def main():
    print("🚀 Football.fun Working Trader")
    print("=" * 40)
    
    token = input("Введите Bearer токен: ").strip()
    if not token:
        print("❌ Токен не может быть пустым!")
        return
    
    trader = FootballTrader(token)
    
    # Покупаем игрока
    result = trader.buy_player(246333, 1)
    
    if result["success"]:
        print(f"\n✅ Готово! Hash: {result['hash']}")
    else:
        print(f"\n❌ Ошибка: {result['error']}")

if __name__ == "__main__":
    main()