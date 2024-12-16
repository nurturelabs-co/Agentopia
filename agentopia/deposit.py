import logging
import time

from eth_account import Account

from agentopia.services.web3_service import Contract
from agentopia.settings import settings

logger = logging.getLogger(__name__)


def get_micropayments_contract(micropayments_address):
    return Contract(
        contract_address=micropayments_address,
        abi_path="./agentopia/abis/MicroPayment.json",
    )


def get_token_contract(token_address):
    return Contract(
        contract_address=token_address,
        abi_path="./agentopia/abis/MockUSDC.json",
    )


def deposit_onchain(private_key: str, deposit_amount: int) -> str:
    """Deposit USDC into Agentopia.

    Args:
        private_key: Private key to sign transactions
        amount: Amount to deposit in USDC (6 decimals)

    Returns:
        Transaction details
    """
    usdc_address = settings.USDC_ADDRESS
    micropayments_address = settings.MICROPAYMENT_ADDRESS
    logger.debug(f"USDC address: {usdc_address}")
    logger.debug(f"Micropayments address: {micropayments_address}")
    usdc = get_token_contract(usdc_address)
    user_address = Account.from_key(private_key).address
    # First approve USDC contract
    # Check and set allowance if needed
    initial_allowance = usdc.read("allowance", user_address, micropayments_address)
    logger.debug(f"Initial allowance: {initial_allowance}")
    assert initial_allowance is not None

    if initial_allowance < deposit_amount:
        usdc.pk_manager.set(private_key)
        tx_hash = usdc.write("approve", micropayments_address, deposit_amount)
        logger.debug(f"Transaction hash for allowance: {tx_hash}")

        # Wait for allowance update
        final_allowance = usdc.read("allowance", user_address, micropayments_address)
        while final_allowance != deposit_amount:
            time.sleep(1)
            final_allowance = usdc.read(
                "allowance", user_address, micropayments_address
            )
            logger.debug(f"Waiting for allowance to update: {final_allowance}")

    # Deposit USDC into micropayments contract
    micropayments = get_micropayments_contract(micropayments_address)
    micropayments.pk_manager.set(private_key)
    initial_contract_balance = micropayments.read("balances", user_address)
    logger.debug(f"Initial contract balance: {initial_contract_balance}")

    tx_hash = micropayments.write("deposit", deposit_amount)
    logger.debug(f"Transaction hash for deposit: {tx_hash}")
    return str(tx_hash)
