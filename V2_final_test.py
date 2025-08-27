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
        """
        Получение котировки для покупки игрока
        
        Args:
            player_id: ID игрока
            shares: Количество акций (по умолчанию 1)
            slippage_bps: Проскальзывание в базисных пунктах (по умолчанию 500 = 5%)
        
        Returns:
            Данные котировки
        """
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
        """
        Получение подписи для торговли
        
        Args:
            quote_uuid: UUID котировки
        
        Returns:
            Данные подписи (signature, nonce, deadline)
        """
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
        """
        Выполнение RPC запроса к блокчейну
        
        Args:
            method: Метод RPC
            params: Параметры запроса
            rpc_id: ID запроса
        
        Returns:
            Результат RPC запроса
        """
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

    def get_gas_prices(self) -> Dict:
        """
        Получение актуальных цен на газ
        
        Returns:
            Словарь с ценами на газ
        """
        print("📤 Получаем актуальные цены на газ...")
        
        # Получаем базовую комиссию и приоритетную комиссию
        base_fee_result = self.rpc_call("eth_gasPrice", [])
        priority_fee_result = self.rpc_call("eth_maxPriorityFeePerGas", [])
        
        # Получаем правильный nonce через EntryPoint
        nonce_result = self.rpc_call("eth_call", [{
            "data": "0x35567e1a0000000000000000000000008f37a8015851976ab75e309100c2511ababc68ad0000000000000000000000000000000000000000000000000000000000000000",
            "to": self.config.entry_point_address
        }, "latest"])
        
        # Конвертируем hex в int
        base_fee = int(base_fee_result, 16)
        priority_fee = int(priority_fee_result, 16)
        
        # Добавляем буфер 20% для надежности
        max_fee = int(base_fee * 1.2)
        max_priority = int(priority_fee * 1.2)
        
        print(f"✅ Газ получен:")
        print(f"   Base fee: {base_fee} ({hex(base_fee)})")
        print(f"   Priority fee: {priority_fee} ({hex(priority_fee)})")
        print(f"   Max fee (с буфером): {max_fee} ({hex(max_fee)})")
        print(f"   Max priority (с буфером): {max_priority} ({hex(max_priority)})")
        print(f"   Nonce: {nonce_result}")
        
        return {
            "base_fee": base_fee,
            "priority_fee": priority_fee,
            "max_fee_per_gas": max_fee,
            "max_priority_fee_per_gas": max_priority,
            "blockchain_nonce": nonce_result
        }

    def build_call_data(self, player_id: int, max_gold_wei: int, signature: str, nonce: int, deadline: int) -> str:
        """
        Построение callData для смарт-контракта
        
        Args:
            player_id: ID игрока
            max_gold_wei: Максимальное количество золота в wei
            signature: Подпись транзакции
            nonce: Nonce из API
            deadline: Deadline транзакции
        
        Returns:
            Hex строка callData
        """
        print("🔧 Строим callData с актуальными данными...")
        print(f"   Player ID: {player_id}")
        print(f"   Max Gold Wei: {max_gold_wei} ({hex(max_gold_wei)})")
        print(f"   API Nonce: {nonce}")
        print(f"   Deadline: {deadline} ({hex(deadline)})")
        print(f"   Signature: {signature[:20]}...")
        
        # Функция buyShares(uint256[] calldata playerIds, uint256[] calldata maxGoldAmounts, uint256 nonce, uint256 deadline, bytes calldata signature)
        # Selector: 0x34fcd5be
        
        # Начинаем с селектора функции
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
        # Длина массива (1 элемент)
        call_data += "0000000000000000000000000000000000000000000000000000000000000001"
        # Player ID
        call_data += f"{player_id:064x}"
        
        # Массив maxGoldAmounts
        # Длина массива (1 элемент)
        call_data += "0000000000000000000000000000000000000000000000000000000000000001"
        # Max gold amount
        call_data += f"{max_gold_wei:064x}"
        
        # Signature
        signature_clean = signature[2:] if signature.startswith('0x') else signature
        signature_length = len(signature_clean) // 2
        
        # Длина подписи
        call_data += f"{signature_length:064x}"
        # Данные подписи
        call_data += signature_clean
        # Padding до кратности 32 байт
        padding_needed = (32 - (signature_length % 32)) % 32
        call_data += "00" * padding_needed
        
        print(f"✅ CallData построен: {len(call_data)} символов")
        return call_data

    def estimate_user_operation_gas(self, user_op: Dict) -> Dict:
        """
        Оценка газа для UserOperation
        
        Args:
            user_op: UserOperation
        
        Returns:
            Результат оценки газа
        """
        print("📤 Оцениваем газ для UserOperation...")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_estimateUserOperationGas",
            "params": [user_op, self.config.entry_point_address]
        }
        
        response = self.session.post(
            self.config.coinbase_paymaster_url,
            headers=self.rpc_headers,
            json=payload
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка оценки газа: {response.status_code}")
            print(f"   Ответ: {response.text}")
            return {}
        
        result = response.json()
        if "error" in result:
            print(f"⚠️ Ошибка оценки газа: {result['error']}")
            # Возвращаем разумные значения по умолчанию
            return {
                "preVerificationGas": "0x6b9f",  # 27551
                "verificationGasLimit": "0x1b7740",  # 1800000
                "callGasLimit": "0x39bb8"  # 236472
            }
        
        gas_estimates = result["result"]
        print(f"✅ Оценка газа получена:")
        print(f"   PreVerificationGas: {gas_estimates.get('preVerificationGas', '0x6b9f')}")
        print(f"   VerificationGasLimit: {gas_estimates.get('verificationGasLimit', '0x1b7740')}")
        print(f"   CallGasLimit: {gas_estimates.get('callGasLimit', '0x39bb8')}")
        
        return gas_estimates

    def get_paymaster_data(self, user_op: Dict) -> str:
        """
        Получение данных paymaster'а
        
        Args:
            user_op: UserOperation
        
        Returns:
            Paymaster data в hex формате
        """
        print("📤 Получаем данные paymaster...")
        
        # Правильные параметры для Coinbase paymaster
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "pm_getPaymasterStubData",
            "params": [user_op, self.config.entry_point_address, "8453", {}]
        }
        
        response = self.session.post(
            self.config.coinbase_paymaster_url,
            headers=self.rpc_headers,
            json=payload
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка paymaster: {response.status_code}")
            print(f"   Ответ: {response.text}")
            return "0x"
        
        result = response.json()
        if "error" in result:
            print(f"⚠️ Ошибка paymaster: {result['error']}")
            return "0x"
        
        paymaster_data = result["result"]["paymasterAndData"]
        print(f"✅ Paymaster данные получены: {paymaster_data[:50]}...")
        return paymaster_data

    def get_paymaster_and_data(self, user_op: Dict) -> str:
        """
        Получение финальных данных paymaster'а для спонсирования транзакции
        
        Args:
            user_op: UserOperation
        
        Returns:
            Paymaster and data в hex формате
        """
        print("📤 Получаем финальные данные paymaster...")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "pm_getPaymasterAndData",
            "params": [user_op, self.config.entry_point_address, "8453", {}]
        }
        
        response = self.session.post(
            self.config.coinbase_paymaster_url,
            headers=self.rpc_headers,
            json=payload
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка финального paymaster: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
            # Пробуем альтернативный метод
            print("📤 Пробуем альтернативный метод sponsorUserOperation...")
            alt_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "pm_sponsorUserOperation",
                "params": [user_op, self.config.entry_point_address]
            }
            
            alt_response = self.session.post(
                self.config.coinbase_paymaster_url,
                headers=self.rpc_headers,
                json=alt_payload
            )
            
            if alt_response.status_code == 200:
                alt_result = alt_response.json()
                if "result" in alt_result:
                    paymaster_data = alt_result["result"]["paymasterAndData"]
                    print(f"✅ Альтернативные данные paymaster получены: {paymaster_data[:50]}...")
                    return paymaster_data
            
            return "0x"
        
        result = response.json()
        if "error" in result:
            print(f"⚠️ Ошибка финального paymaster: {result['error']}")
            return "0x"
        
        paymaster_data = result["result"]["paymasterAndData"]
        print(f"✅ Финальные данные paymaster получены: {paymaster_data[:50]}...")
        return paymaster_data

    def send_user_operation(self, user_op: Dict) -> Dict:
        """
        Отправка UserOperation
        
        Args:
            user_op: UserOperation для отправки
        
        Returns:
            Результат отправки
        """
        print("📤 Отправляем UserOperation...")
        print(f"   Sender: {user_op['sender']}")
        print(f"   Nonce: {user_op['nonce']}")
        print(f"   CallData: {user_op['callData'][:50]}...")
        print(f"   CallGasLimit: {user_op['callGasLimit']}")
        print(f"   MaxFeePerGas: {user_op['maxFeePerGas']}")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_sendUserOperation",
            "params": [user_op, self.config.entry_point_address]
        }
        
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
            print(f"❌ Ошибка в ответе: {result['error']}")
            return {"error": "Send failed", "details": result}
        
        print(f"✅ UserOperation отправлен: {result['result']}")
        return {"success": True, "userOpHash": result["result"]}

    def buy_player_complete(self, player_id: int, shares: int = 1) -> Dict:
        """
        Полный процесс покупки игрока с правильными параметрами газа
        
        Args:
            player_id: ID игрока для покупки
            shares: Количество акций
        
        Returns:
            Результат покупки
        """
        try:
            print(f"🔄 Покупка игрока {player_id} с правильными параметрами газа...")
            
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
            
            # 3. Получаем актуальные цены на газ
            print("\n3️⃣ Получаем актуальные цены на газ...")
            gas_data = self.get_gas_prices()
            blockchain_nonce = gas_data["blockchain_nonce"]
            
            # Форматируем nonce правильно
            if isinstance(blockchain_nonce, str) and blockchain_nonce.startswith('0x'):
                # Убираем ведущие нули, но оставляем как минимум 1
                formatted_nonce = hex(int(blockchain_nonce, 16))
            else:
                formatted_nonce = blockchain_nonce
            
            # 4. Строим callData
            print("\n4️⃣ Строим callData с актуальными данными...")
            call_data = self.build_call_data(
                player_id, max_gold_wei, signature, api_nonce, deadline
            )
            
            # 5. Создаем базовый UserOperation для оценки газа
            print("\n5️⃣ Создаем UserOperation...")
            base_user_op = {
                "sender": self.config.smart_wallet_address,
                "nonce": formatted_nonce,
                "initCode": "0x",
                "callData": call_data,
                "callGasLimit": "0x39bb8",  # Начальная оценка
                "verificationGasLimit": "0x1b7740",
                "preVerificationGas": "0x6b9f",  # Минимальное значение
                "maxFeePerGas": hex(gas_data["max_fee_per_gas"]),
                "maxPriorityFeePerGas": hex(gas_data["max_priority_fee_per_gas"]),
                "paymasterAndData": "0x",
                "signature": "0x"
            }
            
            # 6. Оцениваем газ
            print("\n6️⃣ Оцениваем газ...")
            gas_estimates = self.estimate_user_operation_gas(base_user_op)
            
            # Обновляем параметры газа
            if gas_estimates:
                base_user_op["preVerificationGas"] = gas_estimates.get("preVerificationGas", "0x6b9f")
                base_user_op["verificationGasLimit"] = gas_estimates.get("verificationGasLimit", "0x1b7740")
                base_user_op["callGasLimit"] = gas_estimates.get("callGasLimit", "0x39bb8")
            
            # 7. Используем фиксированные данные paymaster из реальных запросов
            print("\n7️⃣ Используем фиксированные данные paymaster...")
            # Это данные paymaster из ваших curl запросов
            paymaster_address = "0x2faeb0760d4230ef2ac21496bb4f0b47d634fd4c"
            deadline_hex = hex(deadline)[2:].zfill(8)
            paymaster_data = f"{paymaster_address}000{deadline_hex}0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
            base_user_op["paymasterAndData"] = f"0x{paymaster_data}"
            print(f"✅ Paymaster данные установлены: {paymaster_data[:50]}...")
            
            # 8. Отправляем UserOperation
            print("\n8️⃣ Отправляем UserOperation...")
            result = self.send_user_operation(base_user_op)
            
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
    print("🚀 Football.fun Player Trader v2.0")
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
        result = trader.buy_player_complete(player_id, shares)
        
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