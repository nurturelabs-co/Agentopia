from decimal import Decimal
from pprint import pprint

import pytest
import requests
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
        self.pf = Agentopia(
            api_url=self.api_url,
            private_key=self.test_key,
            micropayment_address="0xF461d09EB295f1538a6fec92072eB2F3578e121a",
            usdc_address="0x8d63C7203d88c95c30C68283c34F743e061c2a31",
            rpc=self.rpc_url,
            chain_id=31337,
        )

    def teardown_method(self) -> None:
        try:
            self.pf.session.close()
        except AttributeError:
            pass

    def test_register_and_execute_service_via_proxy_with_signature(self) -> None:
        # Generate unique slug using timestamp
        balance = self.pf.get_balance()
        initial_balance = balance.available_balance
        print(f"Initial balance: {initial_balance}")
        unique_slug = "hello-world-service"

        base_url = "http://localhost:8890/hello-world-service"
        # Fetch OpenAPI schema
        api_schema = requests.get(f"{base_url}/openapi.json").json()

        # Try to get existing service
        try:
            service = self.pf.service.get_by_slug(slug=unique_slug)
        except Exception as e:
            print(e)
            # Register new hello world service if not found
            service = self.pf.service.register(
                name="Hello World Service",
                description="A simple service to demonstrate the Agentopia.xyz platform",
                base_url=base_url,
                slug=unique_slug,
                initial_hold_amount=Decimal("10"),  # $0.1 USDC
                initial_hold_expires_in=3600,  # 1 hour
                api_schema=api_schema,
            )

        # Verify service response
        assert isinstance(service, AgentopiaServiceModel)
        assert service.name == "Hello World Service"
        assert (
            service.description
            == "A simple service to demonstrate the Agentopia.xyz platform"
        )
        # assert service.base_url == base_url
        assert service.slug == unique_slug
        assert Decimal(service.default_hold_amount) == Decimal("10")
        assert service.default_hold_expires_in == 3600
        assert service.api_schema == api_schema

        # Run the hello world service
        response = self.pf.service.execute_via_proxy(
            service_slug=unique_slug, endpoint_path="hello_world", method="GET"
        )

        pprint(response)

        # Verify response
        assert isinstance(response, dict)
        assert response["message"] == "Hello from Agentopia!"

        # Verify balance
        balance = self.pf.get_balance()
        assert balance.available_balance + 1 == initial_balance

    def test_register_and_execute_service_via_proxy_with_api_key(self) -> None:
        # Generate unique slug using timestamp
        unique_slug = "hello-world-service"
        base_url = "http://localhost:8890/hello-world-service"
        # Fetch OpenAPI schema
        api_schema = requests.get(f"{base_url}/openapi.json").json()

        # Try to get existing service
        try:
            self.pf.service.get_by_slug(slug=unique_slug)
        except Exception as e:
            print(e)
            # Register new hello world service if not found
            self.pf.service.register(
                name="Hello World Service",
                description="A simple service to demonstrate the Agentopia.xyz platform",
                base_url=base_url,
                slug=unique_slug,
                initial_hold_amount=Decimal("10"),  # $0.1 USDC
                initial_hold_expires_in=3600,  # 1 hour
                api_schema=api_schema,
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
        assert balance.available_balance + 1 == initial_balance

    def test_register_and_execute_service_via_direct_call(self) -> None:
        # Generate unique slug using timestamp
        balance = self.pf.get_balance()
        print(f"Initial balance: {balance}")
        initial_balance = balance.available_balance

        unique_slug = "hello-world-service"
        base_url = "http://localhost:8890/hello-world-service"

        # Fetch OpenAPI schema
        api_schema = requests.get(f"{base_url}/openapi.json").json()

        # Try to get existing service
        try:
            service = self.pf.service.get_by_slug(slug=unique_slug)
        except Exception as e:
            print(e)
            # Register new hello world service if not found
            service = self.pf.service.register(
                name="Hello World Service",
                description="A simple service to demonstrate the Agentopia.xyz platform",
                base_url=base_url,
                slug=unique_slug,
                initial_hold_amount=Decimal("10"),  # $0.00001 USDC
                initial_hold_expires_in=3600,  # 1 hour
                api_schema=api_schema,
            )

        pprint(service)

        # Verify service response
        assert isinstance(service, AgentopiaServiceModel)
        assert service.name == "Hello World Service"
        assert (
            service.description
            == "A simple service to demonstrate the Agentopia.xyz platform"
        )
        # assert service.base_url == base_url
        assert service.slug == unique_slug
        assert Decimal(service.default_hold_amount) == Decimal("10")
        assert service.default_hold_expires_in == 3600
        assert service.api_schema == api_schema

        # Run the hello world service
        response = self.pf.service.execute(
            service_slug=unique_slug, endpoint_path="hello_world", method="GET"
        )

        pprint(response)

        # Verify response
        assert isinstance(response, dict)
        assert response["message"] == "Hello from Agentopia!"

        # Verify balance
        balance = self.pf.get_balance()
        assert balance.available_balance + 1 == initial_balance
