import json
import logging

logger = logging.getLogger(__name__)


def get_abi(
    abi_path: str,
):
    with open(abi_path) as f:
        abi = json.load(f)
    return abi
