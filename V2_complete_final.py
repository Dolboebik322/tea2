import requests
import json
import time
from typing import Dict, Optional

class FootballTrader:
    def __init__(self, bearer_token: str):
        """Инициализация трейдера"""
        self.bearer_token = bearer_token
        self.session = requests.Session()
        
        # Конфигурация
        self.config = type('Config', (), {
            'smart_wallet_address': '0x8f37a8015851976aB75E309100c2511abaBC68AD',
            'entry_point_address': '0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789',
            'api_base_url': 'https://api.pro.football.fun',
            'alchemy_rpc_url': 'https://base-mainnet.g.alchemy.com/v2/CCDNKip23OyFJ7ssex2-O',
            'coinbase_paymaster_url': 'https://api.developer.coinbase.com/rpc/v1/base/Zvs2anqQIBcBNSP8ftgv2Ce0mQMyEtyI'
        })()
        
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
            f"{self.config.api_base_url}/v1/trade/quote",
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
            f"{self.config.api_base_url}/v1/trade/signature/buy",
            headers=self.api_headers,
            json={"quoteId": quote_uuid}
        )
        
        if response.status_code != 200:
            response.raise_for_status()
        
        data = response.json()["data"]
        print(f"✅ Подпись: nonce={data['nonce']}, deadline={data['deadline']}")
        return data

    def get_blockchain_nonce(self) -> str:
        """Получение актуального nonce из блокчейна"""
        print("📤 Получаем nonce из EntryPoint...")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_call",
            "params": [
                {
                    "data": f"0x35567e1a000000000000000000000000{self.config.smart_wallet_address[2:].lower()}0000000000000000000000000000000000000000000000000000000000000000",
                    "to": self.config.entry_point_address
                },
                "latest"
            ]
        }
        
        response = self.session.post(
            self.config.alchemy_rpc_url,
            headers=self.rpc_headers,
            json=payload
        )
        
        if response.status_code != 200:
            return "0x0"
        
        result = response.json()
        if "error" in result:
            return "0x0"
        
        blockchain_nonce = result["result"]
        
        # Форматируем nonce правильно
        if blockchain_nonce and blockchain_nonce != "0x":
            nonce_int = int(blockchain_nonce, 16)
            formatted_nonce = hex(nonce_int)
        else:
            formatted_nonce = "0x0"
        
        print(f"✅ Blockchain nonce: {formatted_nonce}")
        return formatted_nonce

    def build_calldata(self, player_id: int, max_gold_wei: int, signature: str, nonce: int, deadline: int) -> str:
        """Построение callData для batched операции"""
        print("🔧 Строим callData...")
        
        # Batched операция: approve USDC + buyShares
        calldata = "0x34fcd5be"  # executeBatch selector
        calldata += "0000000000000000000000000000000000000000000000000000000000000020"  # offset
        calldata += "0000000000000000000000000000000000000000000000000000000000000002"  # count = 2
        calldata += "0000000000000000000000000000000000000000000000000000000000000040"  # offset 1
        calldata += "0000000000000000000000000000000000000000000000000000000000000120"  # offset 2
        
        # Approve USDC
        calldata += "000000000000000000000000833589fcd6edb6e08f4c7c32d4f71b54bda02913"  # USDC
        calldata += "0000000000000000000000000000000000000000000000000000000000000000"  # value = 0
        calldata += "0000000000000000000000000000000000000000000000000000000000000060"  # data offset
        calldata += "0000000000000000000000000000000000000000000000000000000000000044"  # data length
        calldata += "095ea7b3"  # approve selector
        calldata += "0000000000000000000000009da1bb4e725acc0d96010b7ce2a7244cda446617"  # trade contract
        calldata += f"{max_gold_wei:064x}"  # amount
        calldata += "00000000000000000000000000000000000000000000000000000000"  # padding
        
        # BuyShares
        calldata += "0000000000000000000000009da1bb4e725acc0d96010b7ce2a7244cda446617"  # trade contract
        calldata += "0000000000000000000000000000000000000000000000000000000000000000"  # value = 0
        calldata += "0000000000000000000000000000000000000000000000000000000000000060"  # data offset
        calldata += "00000000000000000000000000000000000000000000000000000000000001e4"  # data length
        calldata += "ea624851"  # buyShares selector
        calldata += "00000000000000000000000000000000000000000000000000000000000000e0"  # playerIds offset
        calldata += "0000000000000000000000000000000000000000000000000000000000000120"  # maxGoldAmounts offset
        calldata += f"{nonce:064x}"  # nonce
        calldata += f"{deadline:064x}"  # deadline
        calldata += f"000000000000000000000000{self.config.smart_wallet_address[2:].lower()}"  # user
        calldata += "0000000000000000000000000000000000000000000000000000000000000160"  # signature offset
        calldata += "0000000000000000000000000000000000000000000000000000000000000001"  # playerIds length
        calldata += f"{player_id:064x}"  # player ID
        calldata += "0000000000000000000000000000000000000000000000000000000000000001"  # maxGoldAmounts length
        calldata += f"{max_gold_wei:064x}"  # max gold amount
        
        # Signature
        signature_clean = signature[2:] if signature.startswith('0x') else signature
        signature_length = len(signature_clean) // 2
        calldata += f"{signature_length:064x}"  # signature length
        calldata += signature_clean  # signature data
        
        # Padding
        padding_needed = (32 - (signature_length % 32)) % 32
        calldata += "00" * padding_needed
        
        print(f"✅ CallData построен: {len(calldata)} символов")
        return calldata

    def format_signature_for_aa(self, api_signature: str) -> str:
        """Преобразование подписи в формат Account Abstraction"""
        print("🔧 Форматируем подпись для AA...")
        
        # Базовая структура для AA подписи
        aa_signature = "0x0000000000000000000000000000000000000000000000000000000000000020"
        aa_signature += "0000000000000000000000000000000000000000000000000000000000000000"
        aa_signature += "0000000000000000000000000000000000000000000000000000000000000040"
        
        # Очищаем API подпись
        clean_signature = api_signature[2:] if api_signature.startswith('0x') else api_signature
        signature_length = len(clean_signature) // 2
        
        # Добавляем длину подписи
        aa_signature += f"{signature_length:064x}"
        # Добавляем саму подпись
        aa_signature += clean_signature
        
        # Padding
        padding_needed = (32 - (signature_length % 32)) % 32
        aa_signature += "00" * padding_needed
        
        print(f"✅ Подпись отформатирована: {len(aa_signature)} символов")
        return aa_signature

    def get_paymaster_data(self, calldata: str, blockchain_nonce: str, api_signature: str) -> Optional[str]:
        """Получение paymaster данных"""
        print("📤 Получаем paymaster данные...")
        
        formatted_signature = self.format_signature_for_aa(api_signature)
        
        # Stub UserOperation для получения paymaster данных
        user_op = {
            "callData": calldata,
            "initCode": "0x",
            "maxFeePerGas": "0x22fac23",
            "maxPriorityFeePerGas": "0x1ab3f0",
            "nonce": blockchain_nonce,
            "sender": self.config.smart_wallet_address,
            "signature": "0x0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000041fffffffffffffffffffffffffffffff0000000000000000000000000000000007aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa1c00000000000000000000000000000000000000000000000000000000000000",
            "callGasLimit": "0x0",
            "verificationGasLimit": "0x0",
            "preVerificationGas": "0x0"
        }
        
        payload = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "pm_getPaymasterStubData",
            "params": [user_op, self.config.entry_point_address, "0x2105", None]
        }
        
        response = self.session.post(
            self.config.coinbase_paymaster_url,
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

    def send_user_operation(self, calldata: str, paymaster_data: str, blockchain_nonce: str, api_signature: str) -> Dict:
        """Отправка UserOperation"""
        print("📤 Отправляем UserOperation...")
        
        formatted_signature = self.format_signature_for_aa(api_signature)
        
        user_op = {
            "callData": calldata,
            "callGasLimit": "0x39bb8",
            "initCode": "0x",
            "maxFeePerGas": "0x22fac23",
            "maxPriorityFeePerGas": "0x1ab3f0",
            "nonce": blockchain_nonce,
            "paymasterAndData": paymaster_data,
            "preVerificationGas": "0xdbbf",
            "sender": self.config.smart_wallet_address,
            "signature": formatted_signature,
            "verificationGasLimit": "0x141e9"
        }
        
        payload = {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "eth_sendUserOperation",
            "params": [user_op, self.config.entry_point_address]
        }
        
        print(f"📋 Отправляем UserOperation:")
        print(f"   Nonce: {blockchain_nonce}")
        print(f"   CallGasLimit: {user_op['callGasLimit']}")
        print(f"   PaymasterData: {paymaster_data[:50]}...")
        
        response = self.session.post(
            self.config.coinbase_paymaster_url,
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
        print(f"✅ UserOperation отправлен: {user_op_hash}")
        return {"success": True, "hash": user_op_hash}

    def wait_for_transaction_receipt(self, user_op_hash: str, timeout: int = 60) -> Optional[Dict]:
        """Ожидание подтверждения транзакции"""
        print(f"⏳ Ожидаем подтверждение транзакции {user_op_hash}...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Проверяем статус UserOperation через Alchemy
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_getUserOperationReceipt",
                    "params": [user_op_hash]
                }
                
                response = self.session.post(
                    self.config.alchemy_rpc_url,
                    headers=self.rpc_headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "result" in result and result["result"]:
                        receipt = result["result"]
                        print(f"✅ Транзакция подтверждена!")
                        print(f"   Block: {receipt.get('blockNumber', 'N/A')}")
                        print(f"   Transaction Hash: {receipt.get('transactionHash', 'N/A')}")
                        print(f"   Success: {receipt.get('success', False)}")
                        return receipt
                    elif "error" in result:
                        print(f"⚠️ Ошибка получения receipt: {result['error']}")
                
                # Также проверяем через Coinbase paymaster
                response2 = self.session.post(
                    self.config.coinbase_paymaster_url,
                    headers=self.rpc_headers,
                    json=payload
                )
                
                if response2.status_code == 200:
                    result2 = response2.json()
                    if "result" in result2 and result2["result"]:
                        receipt = result2["result"]
                        print(f"✅ Транзакция подтверждена через paymaster!")
                        return receipt
                
                print(f"⏳ Транзакция еще не подтверждена, ждем... ({int(time.time() - start_time)}s)")
                time.sleep(3)
                
            except Exception as e:
                print(f"⚠️ Ошибка при проверке статуса: {e}")
                time.sleep(3)
        
        print(f"⏰ Timeout: транзакция не подтверждена за {timeout} секунд")
        return None

    def buy_player_complete(self, player_id: int, shares: int = 1) -> Dict:
        """Полный процесс покупки игрока с ожиданием подтверждения"""
        try:
            print(f"🔄 Покупка игрока {player_id} с подтверждением...")
            
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
            
            # 3. Blockchain nonce
            print("\n3️⃣ Получаем blockchain nonce...")
            blockchain_nonce = self.get_blockchain_nonce()
            
            # 4. CallData
            print("\n4️⃣ Строим callData...")
            calldata = self.build_calldata(player_id, max_gold_wei, signature, nonce, deadline)
            
            # 5. Paymaster данные
            print("\n5️⃣ Получаем paymaster данные...")
            paymaster_data = self.get_paymaster_data(calldata, blockchain_nonce, signature)
            
            if not paymaster_data:
                return {"success": False, "error": "Не удалось получить paymaster данные"}
            
            # 6. Отправка UserOperation
            print("\n6️⃣ Отправляем UserOperation...")
            send_result = self.send_user_operation(calldata, paymaster_data, blockchain_nonce, signature)
            
            if "error" in send_result:
                return {"success": False, "error": send_result["error"]}
            
            user_op_hash = send_result["hash"]
            
            # 7. Ожидание подтверждения
            print("\n7️⃣ Ожидаем подтверждение...")
            receipt = self.wait_for_transaction_receipt(user_op_hash, timeout=120)
            
            if receipt:
                print(f"\n🎉 Покупка успешно завершена!")
                print(f"   Player ID: {player_id}")
                print(f"   Shares: {shares}")
                print(f"   UserOp Hash: {user_op_hash}")
                print(f"   Transaction Hash: {receipt.get('transactionHash', 'N/A')}")
                print(f"   Block: {receipt.get('blockNumber', 'N/A')}")
                print(f"   Basescan: https://basescan.org/tx/{receipt.get('transactionHash', '')}")
                
                return {
                    "success": True,
                    "player_id": player_id,
                    "shares": shares,
                    "user_op_hash": user_op_hash,
                    "transaction_hash": receipt.get('transactionHash'),
                    "block_number": receipt.get('blockNumber'),
                    "receipt": receipt,
                    "max_gold_spent": max_gold_wei
                }
            else:
                print(f"\n⚠️ Транзакция отправлена, но подтверждение не получено")
                print(f"   UserOp Hash: {user_op_hash}")
                print(f"   Проверьте статус на: https://basescan.org")
                
                return {
                    "success": True,  # Транзакция отправлена
                    "pending": True,  # Но еще не подтверждена
                    "player_id": player_id,
                    "shares": shares,
                    "user_op_hash": user_op_hash,
                    "max_gold_spent": max_gold_wei
                }
            
        except Exception as e:
            print(f"\n❌ Ошибка: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

def main():
    print("🚀 Football.fun Complete Trader v3.0")
    print("=" * 50)
    
    token = input("Введите Bearer токен: ").strip()
    if not token:
        print("❌ Токен не может быть пустым!")
        return
    
    trader = FootballTrader(token)
    
    # Покупаем игрока
    result = trader.buy_player_complete(246333, 1)
    
    if result["success"]:
        if result.get("pending"):
            print(f"\n⏳ Транзакция отправлена, ожидает подтверждения")
            print(f"   UserOp Hash: {result['user_op_hash']}")
        else:
            print(f"\n✅ Покупка завершена!")
            print(f"   Transaction Hash: {result.get('transaction_hash', 'N/A')}")
    else:
        print(f"\n❌ Ошибка: {result['error']}")

if __name__ == "__main__":
    main()