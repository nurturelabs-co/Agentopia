import time
from decimal import Decimal

import pytest
import requests
from agentopia import Agentopia, AgentopiaServiceModel
from openai import OpenAI


class TestLLMService:
    @pytest.fixture(autouse=True)
    def setup_method(self) -> None:
        # Use test server endpoints
        self.api_url = "http://localhost:8889"
        self.rpc_url = "http://localhost:8545"

        # Create client with test private key
        self.test_key = (
            "0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a"
        )
        self.pf = Agentopia(private_key=self.test_key)

        # Check balance and deposit if needed
        balance = self.pf.get_balance().available_balance
        if balance < 10_000_000:  # 10 USDC (in smallest units)
            tx_hash = self.pf.deposit(10_000_000)
            while True:
                # Wait for balance update
                new_balance = self.pf.get_balance().available_balance
                if new_balance >= 10_000_000:
                    break
                time.sleep(10)

    def teardown_method(self) -> None:
        try:
            self.pf.session.close()
        except AttributeError:
            pass

    def test_register_and_use_llm_service(self) -> None:
        # Generate unique slug
        unique_slug = "llm-service"
        initial_balance = self.pf.get_balance().available_balance

        # Fetch OpenAPI schema
        base_url = "http://localhost:8890/llm-service"
        api_schema = requests.get(f"{base_url}/openapi.json").json()

        # Try to get existing service
        try:
            service = self.pf.service.get_by_slug(slug=unique_slug)
        except Exception as e:
            print(e)
            # Register new LLM service if not found
            service = self.pf.service.register(
                name="LLM Service",
                description="OpenRouter-compatible LLM service",
                base_url=base_url,
                slug=unique_slug,
                default_hold_amount=Decimal("100000"),  # $0.1 USDC (from main.py)
                default_hold_expires_in=600,  # 10 minutes (from main.py)
                api_schema=api_schema,
            )

        # Verify service registration
        assert isinstance(service, AgentopiaServiceModel)
        assert service.name == "LLM Service"
        # assert service.base_url == base_url
        assert service.slug == unique_slug
        assert Decimal(service.default_hold_amount) == Decimal("100000")

        # Create API key
        api_key = self.pf.api_key.create(name="test-llm-key")

        print(
            f"Calling service at {self.api_url}/v1/execute/service/{unique_slug} via OpenAI package"
        )
        # # Test regular completion
        client = OpenAI(
            base_url=f"{self.api_url}/v1/execute/service/{unique_slug}",
            api_key=api_key.key,
        )

        # print("Testing non-streaming completion")
        # completion = client.chat.completions.create(
        #     model="openai/gpt-4o-mini",
        #     messages=[{"role": "user", "content": "Say this is a test"}],
        #     stream=False,
        # )
        # print(completion)
        # print("++++++++++++", completion.choices[0].message.content)
        # assert completion.choices[0].message.content is not None
        # assert len(completion.choices[0].message.content) > 0

        print("Testing streaming completion")
        # Test streaming completion
        streaming_completion = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": "Write a haiku"}],
            stream=True,
        )

        collected_content = ""
        for chunk in streaming_completion:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="")
                collected_content += chunk.choices[0].delta.content
        print()
        assert len(collected_content) > 0

        # Verify balance: it should be decreased by the cost of the request
        final_balance = self.pf.get_balance().available_balance
        assert final_balance < initial_balance

    # def test_llm_service_with_api_key(self) -> None:
    #     # Generate unique slug
    #     unique_slug = f"llm-service-{random.randint(1000, 9999)}"

    #     # Register service
    #     self.pf.service.register(
    #         name="LLM Service",
    #         description="OpenRouter-compatible LLM service",
    #         base_url="http://llm_service:8891",
    #         slug=unique_slug,
    #         initial_hold_amount=Decimal("1000000"),  # $1 USDC
    #         initial_hold_expires_in=3600,  # 1 hour
    #         api_schema_url="http://llm_service:8891/openapi.json",
    #     )

    #     # Create API key
    #     api_key = self.pf.api_key.create(name="test-llm-key")
    #     initial_balance = self.pf.get_balance().available_balance

    #     # Test with API key
    #     client = OpenAI(
    #         base_url=f"{self.api_url}/service/{unique_slug}",
    #         api_key=api_key.key,
    #     )

    #     completion = client.chat.completions.create(
    #         model="gpt-3.5-turbo",
    #         messages=[{"role": "user", "content": "Say this is a test"}],
    #     )

    #     assert completion.choices[0].message.content is not None
    #     assert len(completion.choices[0].message.content) > 0

    #     # Verify balance unchanged since we own the service
    #     final_balance = self.pf.get_balance().available_balance
    #     assert final_balance == initial_balance
