import base64
import time
from decimal import Decimal
from enum import Enum
from typing import Dict, Optional
from uuid import UUID

import orjson
import requests
from eth_account import Account
from eth_account.messages import encode_defunct
from pydantic import BaseModel

from agentopia.api_key import APIKeyManager
from agentopia.deposit import deposit_onchain
from agentopia.hold import HoldManager
from agentopia.service import ServiceManager
from agentopia.settings import settings
from agentopia.utility import Web3Address


def _json_default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(f"Type is not JSON serializable: {type(obj)}")


class Balance(BaseModel):
    available_balance: int
    # left_to_settle: int
    amount_on_hold: int


class WithdrawalStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class WithdrawalRequestResponse(BaseModel):
    id: int
    amount: int
    status: WithdrawalStatus
    transaction_hash: Optional[str] = None
    error_message: Optional[str] = None
    user_address: Web3Address


class Agentopia:
    def __init__(
        self,
        private_key: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """Initialize the Agentopia client.

        Args:
            private_key: Ethereum private key for signing requests
            api_key: API key for authentication
            api_url: Base URL for the Agentopia API
        """
        self.api_url = settings.PRODUCT_FUN_API.rstrip("/")
        self.session = requests.Session()

        private_key = private_key or settings.USER_PRIVATE_KEY
        api_key = api_key or settings.API_KEY

        if private_key:
            self.account = Account.from_key(private_key)
            self.address = self.account.address
            self._setup_wallet_auth()
        elif api_key:
            self.session.headers["Authorization"] = f"Bearer {api_key}"
        else:
            raise ValueError("Either private_key or api_key must be provided")

        # Add service instance
        # self.services = Service(self)

    @property
    def service(self) -> ServiceManager:
        """Get the service manager."""
        if not hasattr(self, "_service_manager"):
            self._service_manager = ServiceManager(self)
        return self._service_manager

    @property
    def hold(self) -> HoldManager:
        """Get the hold manager."""
        if not hasattr(self, "_hold_manager"):
            self._hold_manager = HoldManager(self)
        return self._hold_manager

    @property
    def api_key(self) -> APIKeyManager:
        """Get the API key manager."""
        if not hasattr(self, "_api_key_manager"):
            self._api_key_manager = APIKeyManager(self)
        return self._api_key_manager

    def _setup_wallet_auth(self):
        """Set up wallet-based authentication."""
        # Get nonce for signing
        resp = self._get(f"/v1/user/{self.address}/nonce")
        print(resp)
        nonce = resp["nonce"]
        resp = self._get("/v1/platform/message_to_sign")
        message = resp["message"]
        # Get message to sign
        message = f"{message}:{nonce}"

        # Sign message
        message_hash = encode_defunct(text=message)
        signed = self.account.sign_message(message_hash)
        signature = signed.signature.hex()

        # Set auth header
        auth = f"{self.address}:{signature}"
        auth_bytes = auth.encode("utf-8")
        auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")
        self.session.headers["Authorization"] = f"Basic {auth_b64}"

    def _get(self, path: str, base_url: Optional[str] = None, **kwargs) -> Dict:
        """Make GET request to API."""
        url = f"{base_url or self.api_url}{path}"
        headers = kwargs.pop("headers", {})
        if base_url:
            # Don't send auth header for external URLs
            session = requests.Session()
            session.headers.update(headers)
            resp = session.get(url, **kwargs)
        else:
            resp = self.session.get(url, headers=headers, **kwargs)
        try:
            print(f"Response text: {resp.text}")
            print(f"Response headers: {resp.headers}")
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"Response text: {resp.text}")
            raise e
        json_resp = resp.json()
        # if "data" not in json_resp:
        #     print(f"Response missing data field: {json_resp}")
        return json_resp.get("data", json_resp)

    def _post(self, path: str, base_url: Optional[str] = None, **kwargs) -> Dict:
        """Make POST request to API."""
        if "json" in kwargs:
            kwargs["data"] = orjson.dumps(kwargs.pop("json"), default=_json_default)
            kwargs["headers"] = {
                **(kwargs.get("headers", {})),
                "Content-Type": "application/json",
            }
        url = f"{base_url or self.api_url}{path}"
        headers = kwargs.pop("headers", {})
        if base_url:
            # Don't send auth header for external URLs
            session = requests.Session()
            session.headers.update(headers)
            resp = session.post(url, **kwargs)
        else:
            resp = self.session.post(url, headers=headers, **kwargs)
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"Response text: {resp.text}")
            raise e
        json_resp = resp.json()
        # if "data" not in json_resp:
        #     print(f"Response missing data field: {json_resp}")
        return json_resp.get("data", json_resp)

    def _put(self, path: str, data=None, **kwargs) -> Dict:
        """Make a PUT request to the API."""
        if "json" in kwargs:
            kwargs["data"] = orjson.dumps(kwargs.pop("json"), default=_json_default)
            kwargs["headers"] = {
                **(kwargs.get("headers", {})),
                "Content-Type": "application/json",
            }
        resp = self.session.put(f"{self.api_url}{path}", data=data, **kwargs)
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"Response text: {resp.text}")
            raise e
        json_resp = resp.json()
        # if "data" not in json_resp:
        #     print(f"Response missing data field: {json_resp}")
        return json_resp.get("data", json_resp)

    def _delete(self, path: str, **kwargs) -> Dict:
        """Make a DELETE request to the API."""
        if "json" in kwargs:
            kwargs["data"] = orjson.dumps(kwargs.pop("json"), default=_json_default)
            kwargs["headers"] = {
                **(kwargs.get("headers", {})),
                "Content-Type": "application/json",
            }
        resp = self.session.delete(f"{self.api_url}{path}", **kwargs)
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"Response text: {resp.text}")
            raise e
        json_resp = resp.json()
        # if "data" not in json_resp:
        #     print(f"Response missing data field: {json_resp}")
        return json_resp.get("data", json_resp)

    def get_balance(self) -> Balance:
        """Get current balance."""
        return Balance(**self._get(f"/v1/user/{self.address}/balance"))

    def create_hold(self, service_id: UUID, amount: int, expires_in: int = 300) -> UUID:
        """Create a new hold.

        Args:
            service_id: ID of the service to create hold for
            amount: Amount to hold in USDC (6 decimals)
            expires_in: Hold expiration time in seconds

        Returns:
            Hold ID
        """
        response = self._post(
            "/v1/hold",
            json={"service_id": service_id, "amount": amount, "expires_in": expires_in},
        )
        return response["hold_id"]

    def get_hold(self, hold_id: UUID) -> Dict:
        """Get details of a specific hold.

        Args:
            hold_id: UUID of the hold to retrieve

        Returns:
            Hold details
        """
        return self._get(f"/v1/hold/{hold_id}")

    def deduct_from_hold(
        self,
        hold_id: UUID,
        deduction_amount: int,
        input_json: Optional[Dict] = None,
        result_json: Optional[Dict] = None,
    ) -> Dict:
        """Deduct from a hold and charge the specified amount.

        Args:
            hold_id: UUID of the hold to deduct from
            deduction_amount: Amount to deduct from the hold
            input_json: Optional input data to store with transaction
            result_json: Optional result data to store with transaction

        Returns:
            Response indicating success
        """
        return self._delete(
            f"/v1/hold/{hold_id}",
            json={
                "deduction_amount": deduction_amount,
                "input_json": input_json,
                "result_json": result_json,
            },
        )

    def run_function(self, function_slug: str, **params) -> Dict:
        """Run a function via the proxy API."""
        return self._post(f"/v1/run/{function_slug}", json=params)

    def withdraw(
        self, amount: Optional[int] = None, wait: bool = False
    ) -> WithdrawalRequestResponse:
        """Withdraw funds.

        Args:
            amount: Amount to withdraw in USDC (6 decimals). If None, withdraws full balance.
            wait: If True, waits for withdrawal to complete before returning

        Returns:
            Dict containing withdrawal details including status, transaction hash, etc.
        """
        return (
            self._initiate_withdraw_and_wait(amount)
            if wait
            else self._initiate_withdraw(amount)
        )

    def _initiate_withdraw(
        self, amount: Optional[int] = None
    ) -> WithdrawalRequestResponse:
        """Withdraw funds.

        Args:
            amount: Amount to withdraw in USDC (6 decimals). If None, withdraws full balance.

        Returns:
            WithdrawalRequestResponse containing withdrawal request details
        """
        response = self._post(
            f"/v1/user/{self.address}/withdrawals",
            params={"amount": amount} if amount else None,
        )
        return WithdrawalRequestResponse(**response)

    def get_withdrawal_status(self, withdrawal_id: int) -> WithdrawalRequestResponse:
        """Get status of a withdrawal.

        Args:
            withdrawal_id: ID of the withdrawal request

        Returns:
            WithdrawalRequestResponse containing withdrawal status, amount, transaction hash, etc.
        """
        response = self._get(f"/v1/user/{self.address}/withdrawals/{withdrawal_id}")
        return WithdrawalRequestResponse(**response)

    def _initiate_withdraw_and_wait(
        self, amount: Optional[int] = None
    ) -> WithdrawalRequestResponse:
        """Initiate a withdrawal and wait for completion.

        Args:
            amount: Amount to withdraw in USDC (6 decimals). If None, withdraws full balance.

        Returns:
            WithdrawalRequestResponse containing final withdrawal status including transaction hash if completed
        """
        withdrawal = self._initiate_withdraw(amount)

        while True:
            status = self.get_withdrawal_status(withdrawal.id)
            if status.status in [
                WithdrawalStatus.COMPLETED,
                WithdrawalStatus.FAILED,
            ]:
                return status
            time.sleep(5)

    def deposit(self, amount: int) -> str:
        """Deposit funds."""
        return deposit_onchain(
            private_key=str(self.account.key.hex()) or settings.USER_PRIVATE_KEY,
            deposit_amount=amount,
        )  # type: ignore

    def register_service(self, **kwargs) -> Dict:
        """Register a service."""
        return self._post("/v1/service", json=kwargs)
