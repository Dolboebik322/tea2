#!/usr/bin/env python3
"""
Football.fun Player Trader v4.2 - Минимальная версия
Использует самые простые параметры для максимальной совместимости
"""

import requests
import json
import time
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class MinimalConfig:
    """Минимальная конфигурация"""
    api_base_url: str = "https://api.pro.football.fun"
    alchemy_rpc_url: str = "https://base-mainnet.g.alchemy.com/v2/CCDNKip23OyFJ7ssex2-O"
    coinbase_paymaster_url: str = "https://api.developer.coinbase.com/rpc/v1/base/Zvs2anqQIBcBNSP8ftgv2Ce0mQMyEtyI"
    entry_point_address: str = "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789"
    smart_wallet_address: str = "0x8f37a8015851976aB75E309100c2511abaBC68AD"
    usdc_address: str = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    trade_contract: str = "0x9da1bb4e725acc0d96010b7ce2a7244cda446617"
    chain_id: str = "0x2105"

class MinimalFootballTrader:
    def __init__(self, bearer_token: str):
        self.config = MinimalConfig()
        self.bearer_token = bearer_token
        self.session = requests.Session()
        
        self.api_headers = {
            "accept": "*/*",
            "authorization": f"Bearer {bearer_token}",
            "content-type": "application/json",
            "origin": "https://pro.football.fun",
            "referer": "https://pro.football.fun/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        self.rpc_headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "origin": "https://pro.football.fun",
            "referer": "https://pro.football.fun/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
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
        print("📤 Получаем подпись...")
        
        payload = {"quoteId": quote_uuid}
        
        response = self.session.post(
            f"{self.config.api_base_url}/v1/trade/signature/buy",
            headers=self.api_headers,
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()["data"]
        print(f"✅ nonce={data['nonce']}, deadline={data['deadline']}")
        return data

    def build_simple_calldata(self, player_id: int, max_gold_wei: int, signature: str, nonce: int, deadline: int) -> str:
        """Простое построение callData"""
        print("🔧 Строим простой callData...")
        
        # Используем точную структуру из успешного примера
        calldata = "0x34fcd5be"  # executeBatch selector
        calldata += "0000000000000000000000000000000000000000000000000000000000000020"  # offset to array
        calldata += "0000000000000000000000000000000000000000000000000000000000000002"  # array length = 2
        calldata += "0000000000000000000000000000000000000000000000000000000000000040"  # offset to first call
        calldata += "0000000000000000000000000000000000000000000000000000000000000120"  # offset to second call
        
        # First call: approve USDC
        calldata += f"000000000000000000000000{self.config.usdc_address[2:].lower()}"  # target
        calldata += "0000000000000000000000000000000000000000000000000000000000000000"  # value = 0
        calldata += "0000000000000000000000000000000000000000000000000000000000000060"  # data offset
        calldata += "0000000000000000000000000000000000000000000000000000000000000044"  # data length
        calldata += "095ea7b3"  # approve selector
        calldata += f"000000000000000000000000{self.config.trade_contract[2:].lower()}"  # spender
        calldata += f"{max_gold_wei:064x}"  # amount
        calldata += "00000000000000000000000000000000000000000000000000000000000000"  # padding
        
        # Second call: buyShares
        calldata += f"000000000000000000000000{self.config.trade_contract[2:].lower()}"  # target
        calldata += "0000000000000000000000000000000000000000000000000000000000000000"  # value = 0
        calldata += "0000000000000000000000000000000000000000000000000000000000000060"  # data offset
        calldata += "00000000000000000000000000000000000000000000000000000000000001e4"  # data length
        
        # buyShares function data
        calldata += "1e4ea624"  # buyShares selector
        calldata += "00000000000000000000000000000000000000000000000000000000000000e0"  # playerIds offset
        calldata += "0000000000000000000000000000000000000000000000000000000000000120"  # maxGoldAmounts offset
        calldata += f"{max_gold_wei:064x}"  # maxGoldToSpend
        calldata += f"{deadline:064x}"  # deadline
        calldata += f"000000000000000000000000{self.config.smart_wallet_address[2:].lower()}"  # recipient
        calldata += "0000000000000000000000000000000000000000000000000000000000000160"  # signature offset
        
        # playerIds array
        calldata += "0000000000000000000000000000000000000000000000000000000000000001"  # length = 1
        calldata += f"{player_id:064x}"  # player ID
        
        # maxGoldAmounts array
        calldata += "0000000000000000000000000000000000000000000000000000000000000001"  # length = 1
        calldata += f"{max_gold_wei:064x}"  # max gold amount
        
        # signature
        clean_sig = signature.replace("0x", "")
        calldata += "0000000000000000000000000000000000000000000000000000000000000041"  # signature length
        calldata += clean_sig  # signature data
        calldata += "00000000000000000000000000000000000000000000000000000000000000"  # padding
        
        print(f"✅ CallData: {len(calldata)} символов")
        return calldata

    def create_minimal_user_operation(self, calldata: str) -> Dict:
        """Создание минимального UserOperation"""
        print("🔧 Создаем минимальный UserOperation...")
        
        # Используем самые простые параметры
        user_op = {
            "callData": calldata,
            "callGasLimit": "0x39bb8",  # Из успешного примера
            "initCode": "0x",
            "maxFeePerGas": "0x50535a6",  # Из успешного примера
            "maxPriorityFeePerGas": "0x1ab3f0",  # Из успешного примера
            "nonce": "0x1",  # Простой nonce
            "paymasterAndData": "0x",  # Без paymaster для простоты
            "preVerificationGas": "0xdd0a",  # Из успешного примера
            "sender": self.config.smart_wallet_address,
            "signature": "0x",  # Пустая подпись для начала
            "verificationGasLimit": "0x141e9"  # Из успешного примера
        }
        
        print("✅ Минимальный UserOperation создан")
        return user_op

    def send_minimal_operation(self, user_op: Dict) -> Optional[str]:
        """Отправка минимального UserOperation"""
        print("📤 Отправляем минимальный UserOperation...")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_sendUserOperation",
            "params": [user_op, self.config.entry_point_address]
        }
        
        print(f"📋 Параметры:")
        print(f"   Nonce: {user_op['nonce']}")
        print(f"   CallGasLimit: {user_op['callGasLimit']}")
        print(f"   MaxFeePerGas: {user_op['maxFeePerGas']}")
        print(f"   PaymasterAndData: {user_op['paymasterAndData']}")
        
        try:
            # Пробуем отправить через Alchemy RPC
            response = self.session.post(
                self.config.alchemy_rpc_url,
                headers=self.rpc_headers,
                json=payload
            )
            
            result = response.json()
            print(f"📥 Ответ Alchemy: {result}")
            
            if "result" in result:
                print(f"✅ Успех через Alchemy: {result['result']}")
                return result["result"]
            
            # Если не получилось через Alchemy, пробуем Coinbase
            print("🔄 Пробуем через Coinbase...")
            
            response = self.session.post(
                self.config.coinbase_paymaster_url,
                headers=self.rpc_headers,
                json=payload
            )
            
            result = response.json()
            print(f"📥 Ответ Coinbase: {result}")
            
            if "result" in result:
                print(f"✅ Успех через Coinbase: {result['result']}")
                return result["result"]
            else:
                print(f"❌ Ошибка: {result.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"❌ Исключение: {e}")
            return None

    def buy_player_minimal(self, player_id: int, shares: int = 1) -> Dict:
        """Минимальная покупка игрока"""
        print(f"\n🚀 Минимальная покупка игрока {player_id}...")
        
        try:
            # 1. Котировка
            print("\n1️⃣ Котировка...")
            quote_data = self.get_quote(player_id, shares)
            max_gold_wei = int(quote_data["totalMaxGoldToSpendWei"])
            
            # 2. Подпись
            print("\n2️⃣ Подпись...")
            signature_data = self.get_signature(quote_data["uuid"])
            
            # 3. CallData
            print("\n3️⃣ CallData...")
            calldata = self.build_simple_calldata(
                player_id, 
                max_gold_wei, 
                signature_data["signature"],
                signature_data["nonce"],
                signature_data["deadline"]
            )
            
            # 4. UserOperation
            print("\n4️⃣ UserOperation...")
            user_op = self.create_minimal_user_operation(calldata)
            
            # 5. Отправка
            print("\n5️⃣ Отправка...")
            result = self.send_minimal_operation(user_op)
            
            if result:
                return {
                    "success": True,
                    "player_id": player_id,
                    "operation_hash": result
                }
            else:
                return {"success": False, "error": "Не удалось отправить операцию"}
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return {"success": False, "error": str(e)}

def main():
    print("🚀 Football.fun Minimal Trader v4.2")
    print("="*50)
    
    bearer_token = input("Введите Bearer токен: ").strip()
    
    if not bearer_token:
        print("❌ Токен не указан!")
        return
    
    trader = MinimalFootballTrader(bearer_token)
    
    player_id = 570810
    shares = 1
    
    result = trader.buy_player_minimal(player_id, shares)
    
    if result["success"]:
        print(f"\n✅ Успех! Игрок {player_id} куплен!")
        print(f"   Hash: {result['operation_hash']}")
    else:
        print(f"\n❌ Ошибка: {result['error']}")

if __name__ == "__main__":
    main()