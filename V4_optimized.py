#!/usr/bin/env python3
"""
Football.fun Player Trader v4.0 - Оптимизированная версия
Убираем статичные запросы, оставляем только необходимые
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
    smart_wallet_address: str = "0x8f37a8015851976aB75E309100c2511abaBC68AD"  # Статичный
    usdc_address: str = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    trade_contract: str = "0x9da1bb4e725acc0d96010b7ce2a7244cda446617"
    chain_id: str = "0x2105"
    
    # Статичные данные (не изменяются)
    wallet_code: str = "0x363d3d373d3d363d7f360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc545af43d6000803e6038573d6000fd5b3d6000f3"

class OptimizedFootballTrader:
    def __init__(self, bearer_token: str):
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
        
        # Заголовки для RPC запросов
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
        print(f"✅ Подпись: nonce={data['nonce']}, deadline={data['deadline']}")
        return data

    def get_current_nonce(self) -> str:
        """Получение текущего nonce из EntryPoint"""
        print("📤 Получаем текущий nonce...")
        
        # Используем точные данные из успешного curl запроса
        # Из успешного примера: "0x35567e1a0000000000000000000000008f37a8015851976ab75e309100c2511ababc68ad00000000000000000000000000000000000000000000000000000198eba23566"
        call_data = "0x35567e1a"  # getNonce selector
        call_data += f"000000000000000000000000{self.config.smart_wallet_address[2:].lower()}"  # sender address
        call_data += "00000000000000000000000000000000000000000000000000000198eba23566"  # key из успешного примера
        
        payload = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "eth_call",
            "params": [
                {
                    "data": call_data,
                    "to": self.config.entry_point_address
                },
                "latest"
            ]
        }
        
        print(f"📋 Запрос nonce:")
        print(f"   Call data: {call_data}")
        print(f"   To: {self.config.entry_point_address}")
        
        response = self.session.post(
            self.config.alchemy_rpc_url,
            headers=self.rpc_headers,
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        print(f"📥 Ответ RPC: {result}")
        
        if "error" in result:
            print(f"❌ Ошибка RPC: {result['error']}")
            # Попробуем с key = 0
            print("🔄 Пробуем с key = 0...")
            
            call_data_zero = "0x35567e1a"
            call_data_zero += f"000000000000000000000000{self.config.smart_wallet_address[2:].lower()}"
            call_data_zero += "0000000000000000000000000000000000000000000000000000000000000000"  # key = 0
            
            payload["params"][0]["data"] = call_data_zero
            
            response = self.session.post(
                self.config.alchemy_rpc_url,
                headers=self.rpc_headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"📥 Ответ с key=0: {result}")
            
            if "error" in result:
                raise Exception(f"Error getting nonce: {result['error']}")
        
        full_nonce = result["result"]
        print(f"✅ Текущий nonce: {full_nonce}")
        
        # Проверяем, что nonce не равен 0x0
        if full_nonce == "0x0000000000000000000000000000000000000000000000000000000000000000":
            print("⚠️ Получен нулевой nonce, используем значение из успешного примера")
            return "0x1"
        
        # Убираем ведущие нули для совместимости с Go парсером
        # Преобразуем в int и обратно в hex без ведущих нулей
        nonce_int = int(full_nonce, 16)
        clean_nonce = hex(nonce_int)
        
        print(f"🔧 Очищенный nonce: {clean_nonce}")
        return clean_nonce

    def get_gas_prices(self) -> Dict:
        """Получение актуальных цен на газ"""
        print("📤 Получаем цены на газ...")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "eth_maxPriorityFeePerGas"
        }
        
        response = self.session.post(
            self.config.alchemy_rpc_url,
            headers=self.rpc_headers,
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        priority_fee = int(result["result"], 16)
        
        # Используем проверенные значения с буфером
        max_fee = priority_fee * 50
        max_priority = priority_fee * 2
        
        gas_prices = {
            "max_fee_per_gas": hex(max_fee),
            "max_priority_fee_per_gas": hex(max_priority)
        }
        
        print(f"✅ Цены на газ: maxFee={hex(max_fee)}, maxPriority={hex(max_priority)}")
        return gas_prices

    def build_calldata(self, player_id: int, max_gold_wei: int, signature: str, nonce: int, deadline: int) -> str:
        """Построение callData"""
        print("🔧 Строим callData...")
        
        # Точно такой же callData как в успешных примерах
        calldata = "0x34fcd5be"
        calldata += "0000000000000000000000000000000000000000000000000000000000000020"
        calldata += "0000000000000000000000000000000000000000000000000000000000000002"
        calldata += "0000000000000000000000000000000000000000000000000000000000000040"
        calldata += "0000000000000000000000000000000000000000000000000000000000000120"
        
        # Approve USDC
        calldata += f"000000000000000000000000{self.config.usdc_address[2:].lower()}"
        calldata += "0000000000000000000000000000000000000000000000000000000000000000"
        calldata += "0000000000000000000000000000000000000000000000000000000000000060"
        calldata += "0000000000000000000000000000000000000000000000000000000000000044"
        calldata += "095ea7b3"
        calldata += f"000000000000000000000000{self.config.trade_contract[2:].lower()}"
        calldata += f"{max_gold_wei:064x}"
        calldata += "00000000000000000000000000000000000000000000000000000000000000"
        
        # BuyShares
        calldata += f"000000000000000000000000{self.config.trade_contract[2:].lower()}"
        calldata += "0000000000000000000000000000000000000000000000000000000000000000"
        calldata += "0000000000000000000000000000000000000000000000000000000000000060"
        calldata += "00000000000000000000000000000000000000000000000000000000000001e4"
        
        # buyShares function call
        calldata += "1e4ea624"
        calldata += "00000000000000000000000000000000000000000000000000000000000000e0"
        calldata += "0000000000000000000000000000000000000000000000000000000000000120"
        calldata += f"{max_gold_wei:064x}"
        calldata += f"{deadline:064x}"
        calldata += f"000000000000000000000000{self.config.smart_wallet_address[2:].lower()}"
        calldata += "0000000000000000000000000000000000000000000000000000000000000160"
        
        # playerIds array
        calldata += "0000000000000000000000000000000000000000000000000000000000000001"
        calldata += f"{player_id:064x}"
        
        # maxGoldAmounts array
        calldata += "0000000000000000000000000000000000000000000000000000000000000001"
        calldata += f"{max_gold_wei:064x}"
        
        # signature
        clean_signature = signature.replace("0x", "")
        calldata += "0000000000000000000000000000000000000000000000000000000000000041"
        calldata += clean_signature
        calldata += "00000000000000000000000000000000000000000000000000000000000000"
        
        print(f"✅ CallData построен: {len(calldata)} символов")
        return calldata

    def get_paymaster_data(self, calldata: str, nonce: str, gas_prices: Dict) -> Dict:
        """Получение paymaster данных (двухэтапно)"""
        print("📤 Получаем paymaster данные...")
        
        # Этап 1: Stub данные
        stub_user_op = {
            "callData": calldata,
            "initCode": "0x",
            "maxFeePerGas": gas_prices["max_fee_per_gas"],
            "maxPriorityFeePerGas": gas_prices["max_priority_fee_per_gas"],
            "nonce": nonce,
            "sender": self.config.smart_wallet_address,
            "signature": "0x0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000041fffffffffffffffffffffffffffffff0000000000000000000000000000000007aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa1c00000000000000000000000000000000000000000000000000000000000000",
            "callGasLimit": "0x0",
            "verificationGasLimit": "0x0",
            "preVerificationGas": "0x0"
        }
        
        # Запрос stub данных
        payload = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "pm_getPaymasterStubData",
            "params": [stub_user_op, self.config.entry_point_address, self.config.chain_id, None]
        }
        
        response = self.session.post(
            self.config.coinbase_paymaster_url,
            headers=self.rpc_headers,
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        if "error" in result:
            raise Exception(f"Paymaster stub error: {result['error']}")
        
        stub_paymaster_data = result["result"]["paymasterAndData"]
        print(f"✅ Stub paymaster данные: {stub_paymaster_data[:50]}...")
        
        # Этап 2: Оценка газа
        gas_user_op = stub_user_op.copy()
        gas_user_op["paymasterAndData"] = stub_paymaster_data
        
        payload = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "eth_estimateUserOperationGas",
            "params": [gas_user_op, self.config.entry_point_address]
        }
        
        response = self.session.post(
            self.config.coinbase_paymaster_url,
            headers=self.rpc_headers,
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        if "error" in result:
            # Используем значения по умолчанию
            gas_estimates = {
                "preVerificationGas": "0xdd0a",
                "callGasLimit": "0x39bb8",
                "verificationGasLimit": "0x141e9"
            }
            print(f"⚠️ Используем газ по умолчанию")
        else:
            gas_estimates = result["result"]
            print(f"✅ Оценка газа: {gas_estimates}")
        
        # Этап 3: Финальные paymaster данные
        final_user_op = {
            "callData": calldata,
            "callGasLimit": gas_estimates["callGasLimit"],
            "initCode": "0x",
            "maxFeePerGas": gas_prices["max_fee_per_gas"],
            "maxPriorityFeePerGas": gas_prices["max_priority_fee_per_gas"],
            "nonce": nonce,
            "paymasterAndData": stub_paymaster_data,
            "preVerificationGas": gas_estimates["preVerificationGas"],
            "sender": self.config.smart_wallet_address,
            "signature": "0x0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000041fffffffffffffffffffffffffffffff0000000000000000000000000000000007aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa1c00000000000000000000000000000000000000000000000000000000000000",
            "verificationGasLimit": gas_estimates["verificationGasLimit"]
        }
        
        payload = {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "pm_getPaymasterData",
            "params": [final_user_op, self.config.entry_point_address, self.config.chain_id, None]
        }
        
        response = self.session.post(
            self.config.coinbase_paymaster_url,
            headers=self.rpc_headers,
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        if "error" in result:
            raise Exception(f"Final paymaster error: {result['error']}")
        
        final_paymaster_data = result["result"]["paymasterAndData"]
        print(f"✅ Финальные paymaster данные: {final_paymaster_data[:50]}...")
        
        return {
            "paymaster_data": final_paymaster_data,
            "gas_estimates": gas_estimates
        }

    def create_signature_placeholder(self) -> str:
        """Создание placeholder подписи для тестирования"""
        # Используем подпись из успешного примера
        successful_signature = "204f724eefb366d739519aa914da9131124927dafaa4a5aeb3d420fba40617a76baed7624821e71ef8b3221f2ccfb8d4e7659896bc4c14b03a21a10bc2999a051c"
        
        aa_signature = "0x0000000000000000000000000000000000000000000000000000000000000020"
        aa_signature += "0000000000000000000000000000000000000000000000000000000000000000"
        aa_signature += "0000000000000000000000000000000000000000000000000000000000000040"
        aa_signature += "0000000000000000000000000000000000000000000000000000000000000041"
        aa_signature += successful_signature
        aa_signature += "00000000000000000000000000000000000000000000000000000000000000"
        
        return aa_signature

    def send_user_operation(self, user_op: Dict) -> str:
        """Отправка UserOperation"""
        print("📤 Отправляем UserOperation...")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "eth_sendUserOperation",
            "params": [user_op, self.config.entry_point_address]
        }
        
        print(f"📋 UserOperation:")
        print(f"   Nonce: {user_op['nonce']}")
        print(f"   MaxFeePerGas: {user_op['maxFeePerGas']}")
        print(f"   CallGasLimit: {user_op['callGasLimit']}")
        
        response = self.session.post(
            self.config.coinbase_paymaster_url,
            headers=self.rpc_headers,
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        if "error" in result:
            raise Exception(f"Send UserOp error: {result['error']}")
        
        user_op_hash = result["result"]
        print(f"✅ UserOperation отправлен: {user_op_hash}")
        return user_op_hash

    def wait_for_receipt(self, user_op_hash: str, timeout: int = 120) -> Optional[Dict]:
        """Ожидание подтверждения"""
        print(f"⏳ Ожидаем подтверждение: {user_op_hash}")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            payload = {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "eth_getUserOperationReceipt",
                "params": [user_op_hash]
            }
            
            response = self.session.post(
                self.config.coinbase_paymaster_url,
                headers=self.rpc_headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result and result["result"]:
                    receipt = result["result"]
                    tx_hash = receipt.get("receipt", {}).get("transactionHash")
                    
                    print(f"🎉 Транзакция подтверждена!")
                    if tx_hash:
                        print(f"   TX: https://basescan.org/tx/{tx_hash}")
                    
                    return receipt
            
            print(f"   Проверяем... ({int(time.time() - start_time)}s)")
            time.sleep(5)
        
        return None

    def buy_player_optimized(self, player_id: int, shares: int = 1) -> Dict:
        """Оптимизированная покупка игрока"""
        print(f"\n🚀 Оптимизированная покупка игрока {player_id}...")
        
        try:
            # 1. Котировка
            print("\n1️⃣ Получаем котировку...")
            quote_data = self.get_quote(player_id, shares)
            max_gold_wei = int(quote_data["totalMaxGoldToSpendWei"])
            
            # 2. Подпись от API
            print("\n2️⃣ Получаем подпись от API...")
            signature_data = self.get_signature(quote_data["uuid"])
            api_signature = signature_data["signature"]
            nonce = signature_data["nonce"]
            deadline = signature_data["deadline"]
            
            # 3. Текущий nonce из блокчейна
            print("\n3️⃣ Получаем nonce из блокчейна...")
            blockchain_nonce = self.get_current_nonce()
            
            # 4. Актуальные цены на газ
            print("\n4️⃣ Получаем цены на газ...")
            gas_prices = self.get_gas_prices()
            
            # 5. CallData
            print("\n5️⃣ Строим callData...")
            calldata = self.build_calldata(player_id, max_gold_wei, api_signature, nonce, deadline)
            
            # 6. Paymaster данные
            print("\n6️⃣ Получаем paymaster данные...")
            paymaster_result = self.get_paymaster_data(calldata, blockchain_nonce, gas_prices)
            
            # 7. Финальный UserOperation
            print("\n7️⃣ Создаем финальный UserOperation...")
            final_signature = self.create_signature_placeholder()
            
            user_op = {
                "callData": calldata,
                "callGasLimit": paymaster_result["gas_estimates"]["callGasLimit"],
                "initCode": "0x",
                "maxFeePerGas": gas_prices["max_fee_per_gas"],
                "maxPriorityFeePerGas": gas_prices["max_priority_fee_per_gas"],
                "nonce": blockchain_nonce,
                "paymasterAndData": paymaster_result["paymaster_data"],
                "preVerificationGas": paymaster_result["gas_estimates"]["preVerificationGas"],
                "sender": self.config.smart_wallet_address,
                "signature": final_signature,
                "verificationGasLimit": paymaster_result["gas_estimates"]["verificationGasLimit"]
            }
            
            # 8. Отправка
            print("\n8️⃣ Отправляем UserOperation...")
            user_op_hash = self.send_user_operation(user_op)
            
            # 9. Ожидание подтверждения
            print("\n9️⃣ Ожидаем подтверждение...")
            receipt = self.wait_for_receipt(user_op_hash)
            
            if receipt:
                return {
                    "success": True,
                    "player_id": player_id,
                    "user_op_hash": user_op_hash,
                    "receipt": receipt
                }
            else:
                return {"success": False, "error": "Timeout"}
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return {"success": False, "error": str(e)}

def main():
    print("🚀 Football.fun Optimized Trader v4.0")
    print("="*50)
    
    bearer_token = input("Введите Bearer токен: ").strip()
    
    if not bearer_token:
        print("❌ Токен не указан!")
        return
    
    trader = OptimizedFootballTrader(bearer_token)
    
    player_id = 570810
    shares = 1
    
    result = trader.buy_player_optimized(player_id, shares)
    
    if result["success"]:
        print(f"\n✅ Успех! Игрок {player_id} куплен!")
    else:
        print(f"\n❌ Ошибка: {result['error']}")

if __name__ == "__main__":
    main()