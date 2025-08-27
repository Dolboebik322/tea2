#!/usr/bin/env python3
"""
Football.fun Player Trader v4.0 - Точная копия curl запросов
Максимально точное воспроизведение успешных curl запросов
"""

import requests
import json
import time
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class TradeConfig:
    """Конфигурация для торговли"""
    api_base_url: str = "https://api.pro.football.fun"
    alchemy_rpc_url: str = "https://base-mainnet.g.alchemy.com/v2/CCDNKip23OyFJ7ssex2-O"
    coinbase_paymaster_url: str = "https://api.developer.coinbase.com/rpc/v1/base/Zvs2anqQIBcBNSP8ftgv2Ce0mQMyEtyI"
    entry_point_address: str = "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789"
    smart_wallet_address: str = "0x8f37a8015851976aB75E309100c2511abaBC68AD"
    usdc_address: str = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    trade_contract: str = "0x9da1bb4e725acc0d96010b7ce2a7244cda446617"

class FootballTrader:
    def __init__(self, bearer_token: str):
        self.config = TradeConfig()
        self.bearer_token = bearer_token
        self.session = requests.Session()
        
        # Заголовки точно как в curl
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
        response.raise_for_status()
        
        data = response.json()["data"]
        print(f"✅ Котировка: UUID={data['uuid']}, Gold={data['totalMaxGoldToSpend']}")
        return data

    def get_signature(self, quote_uuid: str) -> Dict:
        """Получение подписи"""
        print("📤 Получаем подпись...")
        
        payload = {"quoteId": quote_uuid}
        
        response = self.session.post(
            f"{self.config.api_base_url}/v1/trade/signature/buy",
            headers=self.api_headers,
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()["data"]
        print(f"✅ Подпись: nonce={data['nonce']}, deadline={data['deadline']}")
        return data

    def get_current_gas_prices(self) -> Dict:
        """Получение актуальных цен на газ"""
        print("📤 Получаем актуальные цены на газ...")
        
        # Получаем базовую комиссию и приоритетную комиссию
        gas_price_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_gasPrice",
            "params": []
        }
        
        priority_fee_payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "eth_maxPriorityFeePerGas",
            "params": []
        }
        
        # Получаем базовую комиссию
        response1 = self.session.post(
            self.config.alchemy_rpc_url,
            headers=self.rpc_headers,
            json=gas_price_payload
        )
        
        # Получаем приоритетную комиссию
        response2 = self.session.post(
            self.config.alchemy_rpc_url,
            headers=self.rpc_headers,
            json=priority_fee_payload
        )
        
        if response1.status_code == 200 and response2.status_code == 200:
            gas_price_result = response1.json()
            priority_fee_result = response2.json()
            
            if "result" in gas_price_result and "result" in priority_fee_result:
                base_fee = int(gas_price_result["result"], 16)
                priority_fee = int(priority_fee_result["result"], 16)
                
                # Добавляем буфер 50% для надежности
                max_fee = int(base_fee * 1.5)
                max_priority = int(priority_fee * 2.0)
                
                print(f"✅ Актуальные цены на газ:")
                print(f"   Base fee: {base_fee} ({hex(base_fee)})")
                print(f"   Priority fee: {priority_fee} ({hex(priority_fee)})")
                print(f"   Max fee (с буфером): {max_fee} ({hex(max_fee)})")
                print(f"   Max priority (с буфером): {max_priority} ({hex(max_priority)})")
                
                return {
                    "base_fee": base_fee,
                    "priority_fee": priority_fee,
                    "max_fee_per_gas": hex(max_fee),
                    "max_priority_fee_per_gas": hex(max_priority)
                }
        
        # Fallback к более высоким значениям
        print("⚠️ Не удалось получить актуальные цены, используем высокие значения")
        return {
            "base_fee": 50000000,  # 50 gwei
            "priority_fee": 2000000,  # 2 gwei
            "max_fee_per_gas": "0x2faf080",  # 50000000
            "max_priority_fee_per_gas": "0x1e8480"  # 2000000
        }

    def build_exact_calldata(self, player_id: int, max_gold_wei: int, signature: str, nonce: int, deadline: int) -> str:
        """Построение точного callData как в успешном curl"""
        print("🔧 Строим точный callData...")
        
        # Точный callData из успешного curl запроса
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
        calldata += "00000000000000000000000000000000000000000000000000000000000000"  # padding
        
        # BuyShares
        calldata += "0000000000000000000000009da1bb4e725acc0d96010b7ce2a7244cda446617"  # trade contract
        calldata += "0000000000000000000000000000000000000000000000000000000000000000"  # value = 0
        calldata += "0000000000000000000000000000000000000000000000000000000000000060"  # data offset
        calldata += "00000000000000000000000000000000000000000000000000000000000001e4"  # data length (484 bytes)
        
        # buyShares function call
        calldata += "1e4ea624"  # buyShares selector
        calldata += "00000000000000000000000000000000000000000000000000000000000000e0"  # playerIds offset
        calldata += "0000000000000000000000000000000000000000000000000000000000000120"  # maxGoldAmounts offset
        calldata += f"{max_gold_wei:064x}"  # maxGoldToSpend
        calldata += f"{deadline:064x}"  # deadline
        calldata += f"000000000000000000000000{self.config.smart_wallet_address[2:].lower()}"  # user
        calldata += "0000000000000000000000000000000000000000000000000000000000000160"  # signature offset
        
        # playerIds array
        calldata += "0000000000000000000000000000000000000000000000000000000000000001"  # length = 1
        calldata += f"{player_id:064x}"  # player_id
        
        # maxGoldAmounts array  
        calldata += "0000000000000000000000000000000000000000000000000000000000000001"  # length = 1
        calldata += f"{max_gold_wei:064x}"  # max_gold_wei
        
        # signature
        clean_signature = signature.replace("0x", "")
        calldata += "0000000000000000000000000000000000000000000000000000000000000041"  # signature length
        calldata += clean_signature  # signature data
        calldata += "00000000000000000000000000000000000000000000000000000000000000"  # padding
        
        print(f"✅ CallData построен: {len(calldata)} символов")
        return calldata

    def send_exact_useroperation(self, calldata: str, gas_prices: Dict, signature: str, deadline: int) -> Dict:
        """Отправка точного UserOperation как в curl"""
        print("📤 Отправляем точный UserOperation...")
        
        # Точная подпись из успешного curl
        exact_signature = "0x0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000041e16e7eb2993dc27c115a730cd3adaec7f856889bdcc27afaee492201fbe46cd2588a999ec07a75a1222832a123a46eeec37c33903ee53f529fa1496ae836a3201b00000000000000000000000000000000000000000000000000000000000000"
        
        # Точные paymaster данные из успешного curl
        deadline_hex = f"{deadline:08x}"
        paymaster_data = f"0x2faeb0760d4230ef2ac21496bb4f0b47d634fd4c000{deadline_hex}000000000000a583b20c1248462d8ce02d9a0f258b1b0001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000069788b9da7166635d877fa3d86a9d156157b215633cb1eef404f900b5bf2c53367ad10ff3b8dd81d5ca32cefd3e1eb843a9404d89bde4950e9a96950fc7910ca9a0a1b"
        
        user_op = {
            "callData": calldata,
            "callGasLimit": "0x39bb8",
            "initCode": "0x",
            "maxFeePerGas": gas_prices["max_fee_per_gas"],
            "maxPriorityFeePerGas": gas_prices["max_priority_fee_per_gas"],
            "nonce": "0x0",
            "paymasterAndData": paymaster_data,
            "preVerificationGas": "0xdbbf",
            "sender": self.config.smart_wallet_address,
            "signature": exact_signature,
            "verificationGasLimit": "0x141e9"
        }
        
        payload = {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "eth_sendUserOperation",
            "params": [user_op, self.config.entry_point_address]
        }
        
        print(f"📋 Отправляем UserOperation:")
        print(f"   Nonce: {user_op['nonce']}")
        print(f"   CallGasLimit: {user_op['callGasLimit']}")
        print(f"   MaxFeePerGas: {gas_prices['max_fee_per_gas']}")
        print(f"   MaxPriorityFeePerGas: {gas_prices['max_priority_fee_per_gas']}")
        print(f"   PaymasterData: {paymaster_data[:50]}...")
        print(f"   Signature: {exact_signature[:50]}...")
        
        response = self.session.post(
            self.config.alchemy_rpc_url,  # Отправляем через Alchemy
            headers=self.rpc_headers,
            json=payload
        )
        
        print(f"📥 Ответ: {response.status_code}")
        result = response.json()
        
        if "error" in result:
            print(f"❌ RPC ошибка: {result['error']}")
            return {"error": result["error"]}
        
        user_op_hash = result["result"]
        print(f"✅ UserOperation отправлен!")
        print(f"   Hash: {user_op_hash}")
        return {"hash": user_op_hash}

    def wait_for_transaction_receipt(self, user_op_hash: str, timeout: int = 120) -> Optional[Dict]:
        """Ожидание подтверждения транзакции"""
        print(f"⏳ Ожидаем подтверждение транзакции...")
        print(f"   UserOp Hash: {user_op_hash}")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Проверяем в Alchemy
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
                    tx_hash = receipt.get("receipt", {}).get("transactionHash")
                    
                    print(f"\n🎉 Транзакция подтверждена!")
                    print(f"   UserOp Hash: {user_op_hash}")
                    if tx_hash:
                        print(f"   Transaction Hash: {tx_hash}")
                        print(f"   Basescan: https://basescan.org/tx/{tx_hash}")
                    
                    return receipt
            
            print(f"   Проверяем... ({int(time.time() - start_time)}s)")
            time.sleep(5)
        
        print(f"⏰ Timeout: транзакция не подтвердилась за {timeout} секунд")
        return None

    def buy_player(self, player_id: int, shares: int = 1) -> Dict:
        """Покупка игрока - точная копия curl запросов"""
        print(f"\n🚀 Покупка игрока {player_id} (точная копия curl)...")
        
        try:
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
            
            # 3. Цены на газ
            print("\n3️⃣ Получаем цены на газ...")
            gas_prices = self.get_current_gas_prices()
            
            # 4. CallData
            print("\n4️⃣ Строим callData...")
            calldata = self.build_exact_calldata(player_id, max_gold_wei, signature, nonce, deadline)
            
            # 5. Отправка
            print("\n5️⃣ Отправляем UserOperation...")
            send_result = self.send_exact_useroperation(calldata, gas_prices, signature, deadline)
            
            if "error" in send_result:
                return {"success": False, "error": send_result["error"]}
            
            user_op_hash = send_result["hash"]
            
            # 6. Ожидание подтверждения
            print("\n6️⃣ Ожидаем подтверждение...")
            receipt = self.wait_for_transaction_receipt(user_op_hash, timeout=120)
            
            if receipt:
                print(f"\n🎉 Покупка успешно завершена!")
                print(f"   Player ID: {player_id}")
                print(f"   Shares: {shares}")
                print(f"   Gold: {quote_data['totalMaxGoldToSpend']}")
                
                return {
                    "success": True,
                    "player_id": player_id,
                    "shares": shares,
                    "gold_spent": quote_data["totalMaxGoldToSpend"],
                    "user_op_hash": user_op_hash,
                    "receipt": receipt
                }
            else:
                return {"success": False, "error": "Транзакция не подтвердилась"}
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return {"success": False, "error": str(e)}

def main():
    print("🚀 Football.fun Exact Curl Trader v4.0")
    print("="*50)
    
    # Получаем токен от пользователя
    bearer_token = input("Введите Bearer токен: ").strip()
    
    if not bearer_token:
        print("❌ Токен не указан!")
        return
    
    # Создаем трейдера
    trader = FootballTrader(bearer_token)
    
    # Покупаем игрока
    player_id = 246333
    shares = 1
    
    result = trader.buy_player(player_id, shares)
    
    if result["success"]:
        print(f"\n✅ Успех! Игрок {player_id} куплен!")
    else:
        print(f"\n❌ Ошибка: {result['error']}")

if __name__ == "__main__":
    main()