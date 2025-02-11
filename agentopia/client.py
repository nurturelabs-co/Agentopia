import base64
import logging
import time
from decimal import Decimal
from enum import Enum
from typing import Dict, Optional

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

logger = logging.getLogger(__name__)


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
        api_url: Optional[str] = None,
        micropayment_address: Optional[str] = None,
        usdc_address: Optional[str] = None,
        rpc: Optional[str] = None,
        chain_id: Optional[int] = None,
    ):
        """Initialize the Agentopia client.

        Args:
            private_key: Ethereum private key for signing requests
            api_key: API key for authentication
            api_url: Base URL for the Agentopia API
        """
        logger.info("Initializing Agentopia client")
        if api_url:
            self.api_url = api_url.rstrip("/")
        else:
            self.api_url = settings.AGENTOPIA_API.rstrip("/")
        logger.debug(f"Using API URL: {self.api_url}")

        self.session = requests.Session()
        private_key = private_key or settings.AGENTOPIA_USER_PRIVATE_KEY
        if micropayment_address:
            logger.debug(f"Setting custom micropayment address: {micropayment_address}")
            settings.MICROPAYMENT_ADDRESS = micropayment_address
        if usdc_address:
            logger.debug(f"Setting custom USDC address: {usdc_address}")
            settings.USDC_ADDRESS = usdc_address
        if rpc:
            logger.debug(f"Setting custom RPC: {rpc}")
            settings.RPC = rpc
        if chain_id:
            logger.debug(f"Setting custom chain ID: {chain_id}")
            settings.CHAIN_ID = chain_id
        api_key = api_key or settings.API_KEY

        if private_key:
            logger.debug("Using private key authentication")
            self.account = Account.from_key(private_key)
            self.address = self.account.address
            self._setup_wallet_auth()
        elif api_key:
            logger.debug("Using API key authentication")
            self.session.headers["Authorization"] = f"Bearer {api_key}"
        else:
            logger.error("No authentication method provided")
            raise ValueError("Either private_key or api_key must be provided")

        logger.info("Agentopia client initialized successfully")

    @property
    def service(self) -> ServiceManager:
        """Get the service manager."""
        if not hasattr(self, "_service_manager"):
            logger.debug("Initializing service manager")
            self._service_manager = ServiceManager(self)
        return self._service_manager

    @property
    def hold(self) -> HoldManager:
        """Get the hold manager."""
        if not hasattr(self, "_hold_manager"):
            logger.debug("Initializing hold manager")
            self._hold_manager = HoldManager(self)
        return self._hold_manager

    @property
    def api_key(self) -> APIKeyManager:
        """Get the API key manager."""
        if not hasattr(self, "_api_key_manager"):
            logger.debug("Initializing API key manager")
            self._api_key_manager = APIKeyManager(self)
        return self._api_key_manager

    def _setup_wallet_auth(self):
        """Set up wallet-based authentication."""
        logger.info("Setting up wallet authentication")
        # Get nonce for signing
        resp = self._get(f"/v1/user/{self.address}/nonce")
        logger.debug(f"Got nonce response: {resp}")
        nonce = resp["nonce"]
        resp = self._get("/v1/platform/message_to_sign")
        message = resp["message"]
        # Get message to sign
        message = f"{message}:{nonce}"
        logger.debug(f"Message to sign: {message}")

        # Sign message
        message_hash = encode_defunct(text=message)
        signed = self.account.sign_message(message_hash)
        signature = signed.signature.hex()
        logger.debug("Message signed successfully")

        # Set auth header
        auth = f"{self.address}:{signature}"
        auth_bytes = auth.encode("utf-8")
        auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")
        self.session.headers["Authorization"] = f"Basic {auth_b64}"
        logger.info("Wallet authentication setup completed")

    def _get(self, path: str, base_url: Optional[str] = None, **kwargs) -> Dict:
        """Make GET request to API."""
        logger.info(f"Making GET request to {base_url or self.api_url}{path}")
        url = f"{base_url or self.api_url}{path}"
        headers = kwargs.pop("headers", {})
        if base_url:
            logger.debug("Using external URL without auth header")
            session = requests.Session()
            session.headers.update(headers)
            resp = session.get(url, **kwargs)
        else:
            resp = self.session.get(url, headers=headers, **kwargs)
        try:
            logger.debug(f"Response text: {resp.text}")
            logger.debug(f"Response headers: {resp.headers}")
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error occurred in _get: {e}")
            logger.debug(f"Response text: {resp.text}")
            raise e
        json_resp = resp.json()
        logger.debug(f"Parsed JSON response: {json_resp}")
        return json_resp.get("data", json_resp)

    def _post(self, path: str, base_url: Optional[str] = None, **kwargs) -> Dict:
        """Make POST request to API."""
        logger.info(f"Making POST request to {base_url or self.api_url}{path}")
        if "json" in kwargs:
            logger.debug(f"Request JSON payload: {kwargs['json']}")
            kwargs["data"] = orjson.dumps(kwargs.pop("json"), default=_json_default)
            kwargs["headers"] = {
                **(kwargs.get("headers", {})),
                "Content-Type": "application/json",
            }
        url = f"{base_url or self.api_url}{path}"
        headers = kwargs.pop("headers", {})
        if base_url:
            logger.debug("Using external URL without auth header")
            session = requests.Session()
            session.headers.update(headers)
            resp = session.post(url, **kwargs)
        else:
            resp = self.session.post(url, headers=headers, **kwargs)
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error occurred in _post: {e}")
            logger.debug(f"Response text: {resp.text}")
            raise e
        json_resp = resp.json()
        logger.debug(f"Parsed JSON response: {json_resp}")
        return json_resp.get("data", json_resp)

    def _put(self, path: str, data=None, **kwargs) -> Dict:
        """Make a PUT request to the API."""
        logger.info(f"Making PUT request to {self.api_url}{path}")
        if "json" in kwargs:
            logger.debug(f"Request JSON payload: {kwargs['json']}")
            kwargs["data"] = orjson.dumps(kwargs.pop("json"), default=_json_default)
            kwargs["headers"] = {
                **(kwargs.get("headers", {})),
                "Content-Type": "application/json",
            }
            data = None
            resp = self.session.put(f"{self.api_url}{path}", **kwargs)
        else:
            resp = self.session.put(f"{self.api_url}{path}", data=data, **kwargs)
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error occurred in _put: {e}")
            logger.debug(f"Response text: {resp.text}")
            raise e
        json_resp = resp.json()
        logger.debug(f"Parsed JSON response: {json_resp}")
        return json_resp.get("data", json_resp)

    def _delete(self, path: str, **kwargs) -> Dict:
        """Make a DELETE request to the API."""
        logger.info(f"Making DELETE request to {self.api_url}{path}")
        if "json" in kwargs:
            logger.debug(f"Request JSON payload: {kwargs['json']}")
            kwargs["data"] = orjson.dumps(kwargs.pop("json"), default=_json_default)
            kwargs["headers"] = {
                **(kwargs.get("headers", {})),
                "Content-Type": "application/json",
            }
        resp = self.session.delete(f"{self.api_url}{path}", **kwargs)
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.info("+++++++++++++++++++")
            logger.error(f"HTTP error occurred in _delete: {e}")
            logger.info("+++++++++++++++++++")
            logger.info(f"Response text: {resp.text}")
            logger.info("+++++++++++++++++++")

            raise e
        json_resp = resp.json()
        logger.debug(f"Parsed JSON response: {json_resp}")
        return json_resp.get("data", json_resp)

    def get_balance(self) -> Balance:
        """Get current balance."""
        logger.info("Getting balance")
        balance = Balance(**self._get(f"/v1/user/{self.address}/balance"))
        logger.debug(f"Current balance: {balance}")
        return balance

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
        logger.info(f"Initiating withdrawal: amount={amount}, wait={wait}")
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
        logger.info(f"Initiating withdrawal for amount: {amount}")
        response = self._post(
            f"/v1/user/{self.address}/withdrawals",
            params={"amount": amount} if amount else None,
        )
        withdrawal = WithdrawalRequestResponse(**response)
        logger.debug(f"Withdrawal initiated: {withdrawal}")
        return withdrawal

    def get_withdrawal_status(self, withdrawal_id: int) -> WithdrawalRequestResponse:
        """Get status of a withdrawal.

        Args:
            withdrawal_id: ID of the withdrawal request

        Returns:
            WithdrawalRequestResponse containing withdrawal status, amount, transaction hash, etc.
        """
        logger.info(f"Checking withdrawal status for ID: {withdrawal_id}")
        response = self._get(f"/v1/user/{self.address}/withdrawals/{withdrawal_id}")
        status = WithdrawalRequestResponse(**response)
        logger.debug(f"Withdrawal status: {status}")
        return status

    def _initiate_withdraw_and_wait(
        self, amount: Optional[int] = None
    ) -> WithdrawalRequestResponse:
        """Initiate a withdrawal and wait for completion.

        Args:
            amount: Amount to withdraw in USDC (6 decimals). If None, withdraws full balance.

        Returns:
            WithdrawalRequestResponse containing final withdrawal status including transaction hash if completed
        """
        logger.info(f"Initiating withdrawal with wait for amount: {amount}")
        withdrawal = self._initiate_withdraw(amount)

        while True:
            status = self.get_withdrawal_status(withdrawal.id)
            logger.debug(f"Current withdrawal status: {status.status}")
            if status.status in [
                WithdrawalStatus.COMPLETED,
                WithdrawalStatus.FAILED,
            ]:
                logger.info(f"Withdrawal completed with status: {status.status}")
                return status
            time.sleep(5)

    def deposit(self, amount: int) -> str:
        """Deposit funds."""
        logger.info(f"Initiating deposit of {amount}")
        tx_hash = deposit_onchain(
            private_key=str(self.account.key.hex())
            or settings.AGENTOPIA_USER_PRIVATE_KEY,
            deposit_amount=amount,
        )  # type: ignore
        logger.info(f"Deposit transaction hash: {tx_hash}")
        return tx_hash
