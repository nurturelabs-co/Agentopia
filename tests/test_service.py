import random
from decimal import Decimal
from pprint import pprint

import pytest
from agentopia import Agentopia, AgentopiaServiceModel


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

    def teardown_method(self) -> None:
        try:
            self.pf.session.close()
        except AttributeError:
            pass

    def test_register_and_execute_service_via_proxy_with_signature(self) -> None:
        # Generate unique slug using timestamp
        balance = self.pf.get_balance()
        initial_balance = balance.available_balance
        unique_slug = f"hello-world-{random.randint(1000, 9999)}"

        # self.previous_service_slug = unique_slug  # save for next test

        # Register hello world service
        service: AgentopiaServiceModel = self.pf.service.register(
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
        # assert service.service_provider_id == self.pf.address.lower()

        # Run the hello world service
        response = self.pf.service.execute_via_proxy(
            service_slug=unique_slug, endpoint_path="hello_world", method="GET"
        )

        pprint(response)

        # Verify response
        assert isinstance(response, dict)
        assert response["message"] == "Hello from Agentopia!"
        # print(response.get("headers"))
        # assert "X-Usdc-Used" in response.get(
        #     "headers", {}
        # ) or "x-usdc-used" in response.get("headers", {})
        # assert (
        #     response["headers"]["X-Usdc-Used"] == "1"
        #     or response["headers"]["x-usdc-used"] == "1"
        # )  # Charged $0.000001 USDC

        # Verify balance
        balance = self.pf.get_balance()
        assert (
            balance.available_balance == initial_balance
        )  # since the user owns the service no funds should be deducted

    def test_register_and_execute_service_via_proxy_with_api_key(self) -> None:
        # Generate unique slug using timestamp
        unique_slug = f"hello-world-{random.randint(1000, 9999)}"

        # self.previous_service_slug = unique_slug  # save for next test

        # Register hello world service
        self.pf.service.register(
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

        # Verify balance
        balance = self.pf.get_balance()
        assert (
            balance.available_balance == initial_balance
        )  # since the user owns the service no funds should be deducted

    def test_register_and_execute_service_via_direct_call(self) -> None:
        # Generate unique slug using timestamp
        balance = self.pf.get_balance()
        initial_balance = balance.available_balance

        unique_slug = f"hello-world-{random.randint(1000, 9999)}"

        # Register hello world service
        service: AgentopiaServiceModel = self.pf.service.register(
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
        # assert service.service_provider_id == self.pf.address.lower()

        # Run the hello world service
        response = self.pf.service.execute(
            service_slug=unique_slug, endpoint_path="hello_world", method="GET"
        )

        pprint(response)

        # Verify response
        assert isinstance(response, dict)
        assert response["message"] == "Hello from Agentopia!"
        # print(response.get("headers"))
        # assert "X-Usdc-Used" in response.get(
        #     "headers", {}
        # ) or "x-usdc-used" in response.get("headers", {})
        # assert (
        #     response["headers"]["X-Usdc-Used"] == "1"
        #     or response["headers"]["x-usdc-used"] == "1"
        # )  # Charged $0.000001 USDC

        # Verify balance
        balance = self.pf.get_balance()
        assert (
            balance.available_balance == initial_balance
        )  # since the user owns the service no funds should be deducted
