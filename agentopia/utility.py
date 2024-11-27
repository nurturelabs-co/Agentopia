import logging
import math
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

import orjson
from eth_account import Account
from pydantic import BaseModel
from pydantic.functional_validators import AfterValidator
from web3 import Web3
from web3.providers.rpc import HTTPProvider

from agentopia.settings import settings

logger = logging.getLogger(__name__)


def validateAddress(address: str) -> str:
    assert Web3.is_address(address), f"{address} is not a valid address"  # type: ignore
    return Web3.to_checksum_address(address)  # type: ignore


Web3Address = Annotated[str, AfterValidator(validateAddress)]


def validateUSDCAmount(amount: Decimal) -> str:
    assert amount > 0, "Amount must be greater than 0"
    return str(int(amount))


USDCAmount = Annotated[Decimal, AfterValidator(validateUSDCAmount)]


def get_web3(rpc=None):
    provider = HTTPProvider(rpc or settings.RPC, request_kwargs={"timeout": 10})
    web3 = Web3(provider)
    return web3


def get_account(user_pk):
    return Account.from_key(user_pk).address


def get_latest_block(provider):
    block_number = get_web3(provider).eth.blockNumber
    return block_number


def to_wei(x, mul_by=18):
    return x * math.pow(10, mul_by)


def default_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError("Type not serializable")


def dump_json(data: dict) -> str:
    """Dumps a dictionary to JSON string using orjson with default serializer.

    Args:
        data: Dictionary to serialize

    Returns:
        JSON string
    """
    return orjson.dumps(data, default=default_serializer).decode()
