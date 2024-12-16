import time
from decimal import Decimal
from pprint import pprint

import pytest
import requests
from agentopia import Agentopia, AgentopiaServiceModel


class TestFalAIService:
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

    def test_register_and_generate_image(self) -> None:
        # Get initial balance
        balance = self.pf.get_balance()
        initial_balance = balance.available_balance
        print(f"Initial balance: {initial_balance}")

        # Add balance if needed
        if initial_balance < 1000000:  # 1 USDC
            tx_hash = self.pf.deposit(1000000)
            print(f"Deposited 1 USDC, tx hash: {tx_hash}")
            while True:
                balance = self.pf.get_balance()
                if balance.available_balance > initial_balance:
                    break
                time.sleep(10)
            initial_balance = balance.available_balance

        unique_slug = "image-gen-service"
        base_url = "http://localhost:8890/image-gen-service"

        # Fetch OpenAPI schema
        api_schema = requests.get(f"{base_url}/openapi.json").json()

        # Try to get existing service
        try:
            service = self.pf.service.get_by_slug(slug=unique_slug)
        except Exception as e:
            print(e)
            # Register new Image Generation service if not found
            service = self.pf.service.register(
                name="Image Generation Service",
                description="A service to generate images using Flux dev model",
                base_url=base_url,
                slug=unique_slug,
                initial_hold_amount=100000,  # $0.1 USDC
                initial_hold_expires_in=600,  # 10 minutes
                api_schema=api_schema,
            )

        # Verify service response
        assert isinstance(service, AgentopiaServiceModel)
        assert service.name == "Image Generation Service"
        assert (
            service.description == "A service to generate images using Flux dev model"
        )
        assert service.slug == unique_slug
        assert Decimal(service.default_hold_amount) == Decimal("100000")
        assert service.default_hold_expires_in == 600
        assert service.api_schema == api_schema

        # Generate an image
        response = self.pf.service.execute_via_proxy(
            service_slug=unique_slug,
            endpoint_path="gen",
            method="POST",
            json={
                "prompt": "A beautiful sunset over mountains",
                "image_size": {"width": 512, "height": 512},
                "num_images": 1,
            },
        )

        pprint(response)

        # Verify response
        assert isinstance(response, dict)
        assert "images" in response
        assert len(response["images"]) == 1
        image = response["images"][0]
        assert "url" in image
        assert "width" in image
        assert "height" in image
        assert "content_type" in image
        assert image["width"] == 512
        assert image["height"] == 512
        assert image["content_type"] == "image/jpeg"
        assert "has_nsfw_concepts" in response
        assert "prompt" in response
        assert response["prompt"] == "A beautiful sunset over mountains"

        # Verify balance was charged
        balance = self.pf.get_balance()
        expected_cost = (512 * 512 * 1 * 25000) // (10**6)
        assert balance.available_balance + expected_cost == initial_balance
