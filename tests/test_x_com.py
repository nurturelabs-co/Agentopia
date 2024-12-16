from decimal import Decimal
from pprint import pprint

import pytest
import requests
from agentopia import Agentopia, AgentopiaServiceModel

HOLD_AMOUNT = 1000
HOLD_EXPIRES_IN = 600


class TestXComService:
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

    def test_register_and_get_user_details(self) -> None:
        # Get initial balance
        balance = self.pf.get_balance()
        initial_balance = balance.available_balance
        print(f"Initial balance: {initial_balance}")

        unique_slug = "x-com-service"
        base_url = "http://localhost:8890/x-com-service"

        # Fetch OpenAPI schema
        api_schema = requests.get(f"{base_url}/openapi.json").json()

        # Try to get existing service
        try:
            service = self.pf.service.get_by_slug(slug=unique_slug)
        except Exception as e:
            print(e)
            # Register new X.com service if not found
            service = self.pf.service.register(
                name="X.com Service",
                description="A service to get user details, tweets, followers, following, etc. from X.com",
                base_url=base_url,
                slug=unique_slug,
                initial_hold_amount=HOLD_AMOUNT,  # $0.1 USDC
                initial_hold_expires_in=HOLD_EXPIRES_IN,  # 10 minutes
                api_schema=api_schema,
            )

        # Verify service response
        assert isinstance(service, AgentopiaServiceModel)
        assert service.name == "X.com Service"
        assert (
            service.description
            == "A service to get user details, tweets, followers, following, etc. from X.com"
        )
        assert service.slug == unique_slug
        assert Decimal(service.default_hold_amount) == Decimal(HOLD_AMOUNT)
        assert service.default_hold_expires_in == HOLD_EXPIRES_IN
        assert service.api_schema == api_schema

        # Get user details for a test user
        response = self.pf.service.execute_via_proxy(
            service_slug=unique_slug,
            endpoint_path="user/details",
            method="GET",
            params={"username": "elonmusk"},
        )

        pprint(response)

        # Verify response
        assert isinstance(response, dict)
        user = response
        assert user["username"] == "elonmusk"
        assert "follower_count" in user
        assert "following_count" in user
        assert "description" in user

        # Verify balance was charged
        balance = self.pf.get_balance()
        assert balance.available_balance + HOLD_AMOUNT == initial_balance

    def test_get_user_tweets(self) -> None:
        unique_slug = "x-com-service"
        initial_balance = self.pf.get_balance().available_balance

        # Get user tweets
        response = self.pf.service.execute_via_proxy(
            service_slug=unique_slug,
            endpoint_path="user/tweets",
            method="GET",
            params={"username": "elonmusk", "limit": 10, "include_replies": False},
        )

        pprint(response)

        # Verify response
        assert isinstance(response, dict)
        assert "results" in response
        tweets = response["results"]
        # assert len(tweets) <= 10 # this is a bug in https://rapidapi.com/omarmhaimdat/api/twitter154/playground/apiendpoint_4a48b72d-f673-430c-9be3-b8f7c2e2f911, it send 20 tweets irrespective of the limit and then a continuation cursor
        for tweet in tweets:
            assert "tweet_id" in tweet
            assert "text" in tweet
            assert "user" in tweet

        # Verify balance was charged
        balance = self.pf.get_balance()
        assert balance.available_balance + HOLD_AMOUNT == initial_balance

    def test_search_tweets(self) -> None:
        unique_slug = "x-com-service"
        initial_balance = self.pf.get_balance().available_balance

        # Search tweets
        response = self.pf.service.execute_via_proxy(
            service_slug=unique_slug,
            endpoint_path="search/tweets",
            method="GET",
            params={"query": "bitcoin", "section": "top", "limit": 5},
        )

        pprint(response)

        # Verify response
        assert isinstance(response, dict)
        assert "results" in response
        results = response["results"]
        assert len(results) <= 5
        for result in results:
            if "tweet_id" in result:
                assert "text" in result
                assert "user" in result
            else:
                assert "username" in result
                assert "follower_count" in result

        # Verify balance was charged
        balance = self.pf.get_balance()
        assert balance.available_balance + HOLD_AMOUNT == initial_balance
