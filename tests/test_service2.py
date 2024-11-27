import random
import time
from decimal import Decimal
from pprint import pprint

import pytest
from agentopia import Agentopia, AgentopiaServiceModel, WithdrawalStatus


class TestAgentopiaService:
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
        assert self.pf.address == "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65"
        self.test_key2 = (
            "0x8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba"
        )
        self.pf2 = Agentopia(private_key=self.test_key2)
        assert self.pf2.address == "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc"
        # Check balance and deposit if needed
        balance = self.pf.get_balance().available_balance
        if balance < 10_000_000:  # 10 USDC (in smallest units)
            self.pf.deposit(10_000_000)
            while True:
                # Wait for balance update
                new_balance = self.pf.get_balance().available_balance
                if new_balance >= 10_000_000:
                    break
                time.sleep(10)

    def teardown_method(self) -> None:
        try:
            self.pf.session.close()
            self.pf2.session.close()
        except AttributeError:
            pass

    def test_register_and_execute_service_via_proxy_with_signature(self) -> None:
        # Generate unique slug using timestamp
        balance = self.pf.get_balance()
        initial_balance = balance.available_balance
        balance2 = self.pf2.get_balance()
        initial_balance2 = balance2.available_balance
        unique_slug = f"hello-world-{random.randint(1000, 9999)}"

        # Register hello world service with pf2 client
        service: AgentopiaServiceModel = self.pf2.service.register(
            name="Hello World",
            description="A simple hello world service",
            base_url="http://hello_world_service:8890",
            slug=unique_slug,
            initial_hold_amount=Decimal("100000"),  # $0.1 USDC
            initial_hold_expires_in=3600,  # 1 hour
            api_schema_url="http://hello_world_service:8890/openapi.json",
        )

        pprint(service)

        # Verify service response
        assert isinstance(service, AgentopiaServiceModel)
        assert service.name == "Hello World"
        assert service.description == "A simple hello world service"
        assert service.base_url == "http://hello_world_service:8890"
        assert service.slug == unique_slug
        assert Decimal(service.default_hold_amount) == Decimal("100000")
        assert service.default_hold_expires_in == 3600
        assert service.api_schema_url == "http://hello_world_service:8890/openapi.json"

        # Run the hello world service with pf client
        response = self.pf.service.execute_via_proxy(
            service_slug=unique_slug, endpoint_path="hello_world", method="GET"
        )

        pprint(response)

        # Verify response
        assert isinstance(response, dict)
        assert response["message"] == "Hello from Agentopia!"

        # Verify balances
        balance = self.pf.get_balance()
        balance2 = self.pf2.get_balance()
        assert balance2.available_balance == initial_balance2 + 1
        assert balance.available_balance == initial_balance - 1

    def test_register_and_execute_service_via_proxy_with_api_key(self) -> None:
        # Generate unique slug using timestamp
        unique_slug = f"hello-world-{random.randint(1000, 9999)}"

        # Register hello world service with pf2 client
        self.pf2.service.register(
            name="Hello World",
            description="A simple hello world service",
            base_url="http://hello_world_service:8890",
            slug=unique_slug,
            initial_hold_amount=Decimal("100000"),  # $0.1 USDC
            initial_hold_expires_in=3600,  # 1 hour
            api_schema_url="http://hello_world_service:8890/openapi.json",
        )

        api_key = self.pf.api_key.create(name="test-api-key")

        initial_balance = self.pf.get_balance().available_balance
        initial_balance2 = self.pf2.get_balance().available_balance

        new_pf = Agentopia(api_key=api_key.key)
        # Run the hello world service
        response = new_pf.service.execute_via_proxy(
            service_slug=unique_slug,
            endpoint_path="hello_world",
            method="GET",
        )

        pprint(response)

        # Verify response
        assert isinstance(response, dict)
        assert response["message"] == "Hello from Agentopia!"

        # Verify balances
        balance = self.pf.get_balance()
        balance2 = self.pf2.get_balance()
        assert balance2.available_balance == initial_balance2 + 1
        assert balance.available_balance == initial_balance - 1

    def test_register_and_execute_service_via_direct_call(self) -> None:
        # Generate unique slug using timestamp
        balance = self.pf.get_balance()
        initial_balance = balance.available_balance
        balance2 = self.pf2.get_balance()
        initial_balance2 = balance2.available_balance

        unique_slug = f"hello-world-{random.randint(1000, 9999)}"

        # Register hello world service with pf2 client
        service: AgentopiaServiceModel = self.pf2.service.register(
            name="Hello World",
            description="A simple hello world service",
            base_url="http://localhost:8890",
            slug=unique_slug,
            initial_hold_amount=Decimal("100000"),  # $0.1 USDC
            initial_hold_expires_in=3600,  # 1 hour
            api_schema_url="http://hello_world_service:8890/openapi.json",
        )

        pprint(service)

        # Verify service response
        assert isinstance(service, AgentopiaServiceModel)
        assert service.name == "Hello World"
        assert service.description == "A simple hello world service"
        assert service.base_url == "http://localhost:8890"
        assert service.slug == unique_slug
        assert Decimal(service.default_hold_amount) == Decimal("100000")
        assert service.default_hold_expires_in == 3600
        assert service.api_schema_url == "http://hello_world_service:8890/openapi.json"

        # Run the hello world service with pf client
        response = self.pf.service.execute(
            service_slug=unique_slug, endpoint_path="hello_world", method="GET"
        )

        pprint(response)

        # Verify response
        assert isinstance(response, dict)
        assert response["message"] == "Hello from Agentopia!"

        # Verify balances
        balance = self.pf.get_balance()
        balance2 = self.pf2.get_balance()
        # assert balance.available_balance < initial_balance  # pf client paid for service
        # assert (
        #     balance2.available_balance > initial_balance2
        # )  # pf2 client received payment
        assert balance2.available_balance == initial_balance2 + 1
        assert balance.available_balance == initial_balance - 1

        # Service provider (pf2) withdraws their earnings
        withdrawal_amount = balance2.available_balance
        withdrawal_response = self.pf2.withdraw(amount=withdrawal_amount, wait=True)

        # Verify withdrawal completed successfully
        assert withdrawal_response.status == WithdrawalStatus.COMPLETED
        assert withdrawal_response.amount == withdrawal_amount
        assert withdrawal_response.transaction_hash is not None

        # Verify final balance is 0 after withdrawal
        final_balance = self.pf2.get_balance().available_balance
        assert final_balance == 0
