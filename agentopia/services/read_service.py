import logging
from functools import lru_cache

from pipe import select
from web3 import Web3
from web3.exceptions import BadFunctionCallOutput

from agentopia.settings import settings

# from sdk.local_cache import cache
from agentopia.utility import get_web3

logger = logging.getLogger(__name__)

READ_CACHE_TIME = 7


class Cache:
    def __init__(self):
        self._cache = {}

    def get(self, key, default=None):
        return self._cache.get(key, default)

    def set(self, key, value, ex=None):
        self._cache[key] = value

    @lru_cache
    def memoize(self, expire=None):
        def decorator(func):
            return func

        return decorator


cache = Cache()


def get_read_cache_key(
    contract_address, environment, abi, function_name, default_block, *args
):
    fields = [contract_address, environment, function_name, default_block, args]

    signature = "-".join(fields | select(str))
    k = signature

    return k


# read_balance.__cache_key__ = get_read_balance_cache_key


# @cache.memoize(expire=READ_CACHE_TIME)
# @timeit
def read(
    contract_address,
    abi,
    function_name,
    default_block,
    caller_address,
    args,
):
    contract_address = Web3.to_checksum_address(contract_address)

    def get_contract_instance(default_block):
        # print(environment, config.RPC_URL[environment])
        web3 = get_web3()
        web3.eth.default_block = default_block
        return web3.eth.contract(address=contract_address, abi=abi)

    log_dump = f"Read Call: {contract_address}, {settings.CHAIN_ID}, {default_block}, {function_name},  {args}"
    logger.info(log_dump if len(log_dump) < 200 else f"{log_dump[:200]}...")
    # logger.info(f"fetching function_name: {function_name}, args: {args}")
    logger.debug(log_dump)
    try_count = 0

    # logger.info(f"all_providers: {all_providers}")

    try:
        try_count += 1
        # logger.info(f"provider: {provider}")
        if caller_address:
            result = getattr(
                get_contract_instance(default_block).functions,
                function_name,
            )(*args).call({"from": caller_address}, block_identifier=default_block)
        else:
            result = getattr(
                get_contract_instance(default_block).functions,
                function_name,
            )(*args).call(block_identifier=default_block)
        # logger.info(
        #     f"function_name: {function_name}, args: {args}, result: {result}"
        # )

        # Save the result in a permanent cache and then if all the retries are over then return the permanent cached result
        # set_permanent_cache(
        #     result,
        #     contract_address,
        #     environment,
        #     abi,
        #     function_name,
        #     default_block,
        #     index,
        #     args,
        # )

        # Note down this provider and try this as the first provider in the next call

        return result
    except BadFunctionCallOutput as e:
        logger.exception(f"BadFunctionCallOutput: {e}")


read.__cache_key__ = get_read_cache_key


def set_permanent_cache(result, *args):
    cache_key = get_read_cache_key(*args)
    cache_key = f"{cache_key}-permanent"
    cache.set(cache_key, result)


def get_permanent_cache(*args, **kwargs):
    cache_key = get_read_cache_key(*args, **kwargs)
    cache_key = f"{cache_key}-permanent"
    result = cache.get(cache_key)
    if result is None:
        logger.exception("Providers are not working at the moment, failing...")
    return result


def _get_working_provider_key(environment):
    return f"{environment}-working_provider"


def get_working_provider(environment):
    return cache.get(_get_working_provider_key(environment))


def set_working_provider(environment, provider):
    cache.set(_get_working_provider_key(environment), provider)


def save_result_in_cache(
    result,
    contract_address,
    environment,
    abi,
    function_name,
    default_block,
    args,
):
    key = get_read_cache_key(
        contract_address, environment, abi, function_name, default_block, args
    )
    # logger.info(f"Saving result in cache: {key}")
    cache.set(key, result, ex=READ_CACHE_TIME)
    cache.set(key, result, ex=READ_CACHE_TIME)
