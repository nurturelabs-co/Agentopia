import time

import pytest
import requests
from agentopia import Agentopia


class TestAgentopia:
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
        self.agentopia_client = Agentopia(
            api_url=self.api_url,
            private_key=self.test_key,
            micropayment_address="0xF461d09EB295f1538a6fec92072eB2F3578e121a",
            usdc_address="0x8d63C7203d88c95c30C68283c34F743e061c2a31",
            rpc=self.rpc_url,
            chain_id=31337,
        )

    def teardown_method(self) -> None:
        try:
            self.agentopia_client.session.close()
        except AttributeError:
            pass

    def test_get_balance(self) -> None:
        # Get balance for test user
        balance = self.agentopia_client.get_balance()

        # Verify balance response
        # assert isinstance(balance, Balance)
        assert balance.available_balance >= 0

    def test_deposit(self) -> None:
        initial_balance = self.agentopia_client.get_balance().available_balance

        # Deposit USDC into Agentopia
        tx_hash = self.agentopia_client.deposit(1000000)
        assert isinstance(tx_hash, str)
        print(f"Deposit transaction hash: {tx_hash}")
        while True:
            # wait till the balance is updated
            # Get balance for test user
            balance = self.agentopia_client.get_balance()
            if balance.available_balance > initial_balance:
                break
            time.sleep(10)

        assert balance.available_balance == initial_balance + 1000000

    def test_auth_fails_with_wrong_signature(self) -> None:
        # Create client but skip auth setup
        client = Agentopia(private_key=self.test_key)
        client.session.headers.pop("Authorization", None)

        # Make request without auth header
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            resp = client.session.get(
                f"{client.api_url}/v1/user/{client.address}/balance"
            )
            resp.raise_for_status()

        assert exc_info.value.response.status_code == 401
        assert "Not authenticated" in str(exc_info.value.response.text)
