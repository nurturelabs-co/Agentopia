import random
import time

import pytest
from agentopia import Agentopia, WithdrawalStatus


class TestAgentopiaWithdrawal:
    @pytest.fixture(autouse=True)
    def setup_method(self) -> None:
        # Use test server endpoints
        self.api_url = "http://localhost:8889"
        self.rpc_url = "http://localhost:8545"

        # Create client with test private key
        # address = 0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65
        self.test_key = (
            "0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a"
        )
        self.pf = Agentopia(private_key=self.test_key)

    def teardown_method(self) -> None:
        try:
            self.pf.session.close()
        except AttributeError:
            pass

    def test_deposit_use_withdraw(self) -> None:
        # Get initial balance
        initial_balance = self.pf.get_balance().available_balance

        # Deposit USDC into Agentopia
        deposit_amount = 1000000  # $1 USDC
        tx_hash = self.pf.deposit(deposit_amount)
        assert isinstance(tx_hash, str)
        print(f"Deposit transaction hash: {tx_hash}")

        # Wait for deposit to be processed
        while True:
            balance = self.pf.get_balance()
            if balance.available_balance > initial_balance:
                break
            time.sleep(10)

        # Verify deposit
        balance_after_deposit = self.pf.get_balance().available_balance
        assert balance_after_deposit == initial_balance + deposit_amount

        unique_slug = f"hello-world-{random.randint(1000, 9999)}"

        from decimal import Decimal

        # Register hello world service - matching working test_service.py
        service = self.pf.service.register(
            name="Hello World",
            description="A simple hello world service",
            base_url="http://hello_world_service:8890",
            slug=unique_slug,
            initial_hold_amount=Decimal("100000"),  # $0.1 USDC
            initial_hold_expires_in=3600,  # 1 hour
            api_schema_url="http://hello_world_service:8890/openapi.json",
        )

        print(f"Registered service: {service}")

        # Execute service - matching working test_service.py
        response = self.pf.service.execute_via_proxy(
            service_slug=unique_slug,
            endpoint_path="hello_world",  # Removed leading slash
            method="GET",
        )
        print(response)
        assert response["message"] == "Hello from Agentopia!"

        # Get balance after service usage
        balance_after_service = self.pf.get_balance().available_balance

        # Withdraw remaining balance and wait for completion
        withdrawal_amount = balance_after_service
        withdrawal_response = self.pf.withdraw(amount=withdrawal_amount, wait=True)
        assert withdrawal_response.status == WithdrawalStatus.COMPLETED
        assert withdrawal_response.amount == withdrawal_amount
        assert withdrawal_response.transaction_hash is not None

        # Verify final balance is 0
        final_balance = self.pf.get_balance().available_balance
        assert final_balance == 0
