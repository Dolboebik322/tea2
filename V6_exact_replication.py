#!/usr/bin/env python3
"""
Football.fun Player Trader v6.0 - Exact Replication
Точное воспроизведение успешного curl запроса
"""

import requests
import json
import time
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class ExactConfig:
    """Точная конфигурация из успешного примера"""
    api_base_url: str = "https://api.pro.football.fun"
    alchemy_rpc_url: str = "https://base-mainnet.g.alchemy.com/v2/CCDNKip23OyFJ7ssex2-O"
    coinbase_paymaster_url: str = "https://api.developer.coinbase.com/rpc/v1/base/Zvs2anqQIBcBNSP8ftgv2Ce0mQMyEtyI"
    entry_point_address: str = "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789"
    smart_wallet_address: str = "0x8f37a8015851976aB75E309100c2511abaBC68AD"
    chain_id: str = "0x2105"

class ExactReplicationTrader:
    def __init__(self, bearer_token: str):
        self.config = ExactConfig()
        self.bearer_token = bearer_token
        self.session = requests.Session()
        
        # Точные заголовки из curl
        self.api_headers = {
            "accept": "*/*",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "authorization": f"Bearer {bearer_token}",
            "content-type": "application/json",
            "origin": "https://pro.football.fun",
            "priority": "u=1, i",
            "referer": "https://pro.football.fun/",
            "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
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

    def get_quote(self, player_id: int, shares: int) -> Dict:
        """Получение котировки"""
        print(f"📤 Котировка для игрока {player_id}...")
        
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
        response.raise_for_status()
        
        data = response.json()["data"]
        print(f"✅ UUID={data['uuid']}, Gold={data['totalMaxGoldToSpend']}")
        return data

    def get_signature(self, quote_uuid: str) -> Dict:
        """Получение подписи от API"""
        print("📤 Получаем подпись от API...")
        
        payload = {"quoteId": quote_uuid}
        
        response = self.session.post(
            f"{self.config.api_base_url}/v1/trade/signature/buy",
            headers=self.api_headers,
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()["data"]
        print(f"✅ API подпись: nonce={data['nonce']}, deadline={data['deadline']}")
        return data

    def create_static_calldata(self, player_id: int, max_gold_wei: int, api_signature: str, deadline: int) -> str:
        """Создание статичного callData на основе успешного примера"""
        print("🔧 Создаем статичный callData...")
        
        # Используем базовую структуру из успешного curl
        calldata = "0x34fcd5be"  # executeBatch
        calldata += "0000000000000000000000000000000000000000000000000000000000000020"
        calldata += "0000000000000000000000000000000000000000000000000000000000000002"
        calldata += "0000000000000000000000000000000000000000000000000000000000000040"
        calldata += "0000000000000000000000000000000000000000000000000000000000000120"
        
        # First call: approve USDC
        calldata += "000000000000000000000000833589fcd6edb6e08f4c7c32d4f71b54bda02913"  # USDC
        calldata += "0000000000000000000000000000000000000000000000000000000000000000"  # value = 0
        calldata += "0000000000000000000000000000000000000000000000000000000000000060"  # data offset
        calldata += "0000000000000000000000000000000000000000000000000000000000000044"  # data length
        calldata += "095ea7b3"  # approve selector
        calldata += "0000000000000000000000009da1bb4e725acc0d96010b7ce2a7244cda446617"  # trade contract
        calldata += f"{max_gold_wei:064x}"  # amount (динамическое значение)
        calldata += "00000000000000000000000000000000000000000000000000000000000000"  # padding
        
        # Second call: buyShares
        calldata += "0000000000000000000000009da1bb4e725acc0d96010b7ce2a7244cda446617"  # trade contract
        calldata += "0000000000000000000000000000000000000000000000000000000000000000"  # value = 0
        calldata += "0000000000000000000000000000000000000000000000000000000000000060"  # data offset
        calldata += "00000000000000000000000000000000000000000000000000000000000001e4"  # data length
        
        # buyShares function
        calldata += "1e4ea624"  # buyShares selector
        calldata += "00000000000000000000000000000000000000000000000000000000000000e0"
        calldata += "0000000000000000000000000000000000000000000000000000000000000120"
        calldata += f"{max_gold_wei:064x}"  # maxGoldToSpend (динамическое)
        calldata += f"{deadline:064x}"  # deadline (динамическое)
        calldata += "0000000000000000000000008f37a8015851976ab75e309100c2511ababc68ad"  # recipient
        calldata += "0000000000000000000000000000000000000000000000000000000000000160"
        
        # playerIds array (динамическое)
        if player_id == 570810:
            # Для игрока 570810 используем точные данные из curl
            calldata += "000000000000000000000000000000000000000000000000000000000000000a"  # length = 10?
            calldata += "0000000000000000000000000000000000000000000000000000000000000001"  # first element
            calldata += f"{player_id:064x}"  # player ID
        else:
            # Для других игроков используем стандартную структуру
            calldata += "0000000000000000000000000000000000000000000000000000000000000001"
            calldata += f"{player_id:064x}"
        
        # maxGoldAmounts array
        calldata += "0000000000000000000000000000000000000000000000000000000000000001"
        calldata += "0000000000000000000000000000000000000000000000000de0b6b3a7640000"  # 1 ETH в wei
        
        # signature (используем API подпись)
        clean_sig = api_signature.replace("0x", "")
        calldata += "0000000000000000000000000000000000000000000000000000000000000041"
        calldata += clean_sig
        calldata += "00000000000000000000000000000000000000000000000000000000000000"
        
        print(f"✅ CallData создан: {len(calldata)} символов")
        return calldata

    def generate_dynamic_nonce(self) -> str:
        """Генерация динамического nonce в правильном формате"""
        print("🔧 Генерируем динамический nonce...")
        
        # Базовая часть из успешных примеров
        base = "0x198ebc98635"  # Статичная часть
        
        # Добавляем динамическую часть на основе времени
        current_time = int(time.time())
        dynamic_part = f"{current_time % 1000000:016x}"  # 16 hex символов
        
        nonce = base + dynamic_part
        print(f"✅ Nonce: {nonce}")
        return nonce

    def create_placeholder_signature(self) -> str:
        """Создание placeholder подписи как в curl"""
        print("🔧 Создаем placeholder подпись...")
        
        # Точная структура из curl
        signature = "0x0000000000000000000000000000000000000000000000000000000000000020"
        signature += "0000000000000000000000000000000000000000000000000000000000000000"
        signature += "0000000000000000000000000000000000000000000000000000000000000040"
        signature += "0000000000000000000000000000000000000000000000000000000000000041"
        signature += "fffffffffffffffffffffffffffffff0000000000000000000000000000000007aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa1c"
        signature += "00000000000000000000000000000000000000000000000000000000000000"
        
        print(f"✅ Placeholder подпись создана")
        return signature

    def get_paymaster_stub_exact(self, calldata: str, nonce: str) -> Dict:
        """Точное получение paymaster stub данных"""
        print("📤 Получаем paymaster stub (точно как в curl)...")
        
        # Точная структура из curl
        payload = {
            "jsonrpc": "2.0",
            "id": 28,
            "method": "pm_getPaymasterStubData",
            "params": [
                {
                    "callData": calldata,
                    "initCode": "0x",
                    "maxFeePerGas": "0x77521a2",  # Из curl
                    "maxPriorityFeePerGas": "0x1ab3f0",  # Из curl
                    "nonce": nonce,
                    "sender": self.config.smart_wallet_address,
                    "signature": self.create_placeholder_signature(),
                    "callGasLimit": "0x0",  # Для stub запроса
                    "verificationGasLimit": "0x0",  # Для stub запроса
                    "preVerificationGas": "0x0"  # Для stub запроса
                },
                self.config.entry_point_address,
                self.config.chain_id,
                None
            ]
        }
        
        print(f"📋 Paymaster запрос:")
        print(f"   Nonce: {nonce}")
        print(f"   CallData: {calldata[:100]}...")
        
        try:
            response = self.session.post(
                self.config.coinbase_paymaster_url,
                headers=self.rpc_headers,
                json=payload
            )
            
            print(f"📥 Статус: {response.status_code}")
            result = response.json()
            print(f"📥 Ответ: {result}")
            
            if "result" in result:
                return {
                    "success": True,
                    "paymaster_data": result["result"]["paymasterAndData"],
                    "gas_estimates": {
                        "preVerificationGas": result["result"].get("preVerificationGas", "0xdd0a"),
                        "callGasLimit": result["result"].get("callGasLimit", "0x39bb8"),
                        "verificationGasLimit": result["result"].get("verificationGasLimit", "0x141e9")
                    }
                }
            else:
                print(f"❌ Ошибка paymaster: {result.get('error')}")
                return {"success": False, "error": result.get("error")}
                
        except Exception as e:
            print(f"❌ Исключение paymaster: {e}")
            return {"success": False, "error": str(e)}

    def create_working_signature_from_successful_example(self) -> str:
        """Создание рабочей подписи из успешного примера"""
        print("🔧 Используем подпись из успешного примера...")
        
        # Подпись из успешной транзакции (если у вас есть)
        successful_signature = "204f724eefb366d739519aa914da9131124927dafaa4a5aeb3d420fba40617a76baed7624821e71ef8b3221f2ccfb8d4e7659896bc4c14b03a21a10bc2999a051c"
        
        # Форматируем в AA структуру
        aa_signature = "0x0000000000000000000000000000000000000000000000000000000000000020"
        aa_signature += "0000000000000000000000000000000000000000000000000000000000000000"
        aa_signature += "0000000000000000000000000000000000000000000000000000000000000040"
        aa_signature += "0000000000000000000000000000000000000000000000000000000000000041"
        aa_signature += successful_signature
        aa_signature += "00000000000000000000000000000000000000000000000000000000000000"
        
        print(f"✅ Рабочая подпись готова")
        return aa_signature

    def send_final_user_operation(self, user_op: Dict) -> Optional[str]:
        """Отправка финального UserOperation"""
        print("📤 Отправляем финальный UserOperation...")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 30,
            "method": "eth_sendUserOperation",
            "params": [user_op, self.config.entry_point_address]
        }
        
        print(f"📋 Финальный UserOp:")
        print(f"   Nonce: {user_op['nonce']}")
        print(f"   CallGasLimit: {user_op['callGasLimit']}")
        print(f"   MaxFeePerGas: {user_op['maxFeePerGas']}")
        print(f"   PaymasterData: {user_op['paymasterAndData'][:50]}...")
        print(f"   Signature: {user_op['signature'][:50]}...")
        
        try:
            response = self.session.post(
                self.config.coinbase_paymaster_url,
                headers=self.rpc_headers,
                json=payload
            )
            
            result = response.json()
            print(f"📥 Результат отправки: {result}")
            
            if "result" in result:
                return result["result"]
            else:
                print(f"❌ Ошибка отправки: {result.get('error')}")
                return None
                
        except Exception as e:
            print(f"❌ Исключение отправки: {e}")
            return None

    def buy_player_exact_replication(self, player_id: int, shares: int = 1) -> Dict:
        """Точное воспроизведение процесса покупки"""
        print(f"\n🚀 Точное воспроизведение покупки игрока {player_id}...")
        
        try:
            # 1. Котировка
            print("\n1️⃣ Котировка...")
            quote_data = self.get_quote(player_id, shares)
            max_gold_wei = int(quote_data["totalMaxGoldToSpendWei"])
            
            # 2. API подпись
            print("\n2️⃣ API подпись...")
            signature_data = self.get_signature(quote_data["uuid"])
            
            # 3. Динамический nonce
            print("\n3️⃣ Динамический nonce...")
            nonce = self.generate_dynamic_nonce()
            
            # 4. Статичный callData
            print("\n4️⃣ Статичный callData...")
            calldata = self.create_static_calldata(
                player_id, 
                max_gold_wei, 
                signature_data["signature"],
                signature_data["deadline"]
            )
            
            # 5. Paymaster stub
            print("\n5️⃣ Paymaster stub...")
            paymaster_result = self.get_paymaster_stub_exact(calldata, nonce)
            
            if not paymaster_result["success"]:
                return {
                    "success": False,
                    "error": f"Paymaster failed: {paymaster_result['error']}"
                }
            
            # 6. Рабочая подпись
            print("\n6️⃣ Рабочая подпись...")
            final_signature = self.create_working_signature_from_successful_example()
            
            # 7. Финальный UserOperation
            print("\n7️⃣ Финальный UserOperation...")
            user_op = {
                "callData": calldata,
                "callGasLimit": paymaster_result["gas_estimates"]["callGasLimit"],
                "initCode": "0x",
                "maxFeePerGas": "0x77521a2",  # Из curl
                "maxPriorityFeePerGas": "0x1ab3f0",  # Из curl
                "nonce": nonce,
                "paymasterAndData": paymaster_result["paymaster_data"],
                "preVerificationGas": paymaster_result["gas_estimates"]["preVerificationGas"],
                "sender": self.config.smart_wallet_address,
                "signature": final_signature,
                "verificationGasLimit": paymaster_result["gas_estimates"]["verificationGasLimit"]
            }
            
            # 8. Отправка
            print("\n8️⃣ Отправка...")
            result = self.send_final_user_operation(user_op)
            
            if result:
                return {
                    "success": True,
                    "player_id": player_id,
                    "user_op_hash": result,
                    "method": "Exact replication"
                }
            else:
                return {"success": False, "error": "Failed to send UserOperation"}
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return {"success": False, "error": str(e)}

def main():
    print("🚀 Football.fun Exact Replication Trader v6.0")
    print("="*60)
    
    bearer_token = input("Введите Bearer токен: ").strip()
    
    if not bearer_token:
        print("❌ Токен не указан!")
        return
    
    trader = ExactReplicationTrader(bearer_token)
    
    player_id = 570810  # Тот же игрок из curl
    shares = 1
    
    result = trader.buy_player_exact_replication(player_id, shares)
    
    if result["success"]:
        print(f"\n✅ УСПЕХ! Игрок {player_id} куплен!")
        print(f"   UserOp Hash: {result['user_op_hash']}")
        print(f"   Метод: {result['method']}")
    else:
        print(f"\n❌ ОШИБКА: {result['error']}")

if __name__ == "__main__":
    main()