import logging
import time

# defaultdict
from collections import defaultdict
from typing import Dict, List

import requests
from Crypto.Hash import keccak
from eth_account import Account
from hexbytes import HexBytes
from pipe import dedup, groupby, select, where
from web3 import Web3
from web3._utils.events import get_event_data
from web3.gas_strategies.time_based import fast_gas_price_strategy
from web3.logs import IGNORE
from web3.providers.rpc import HTTPProvider

from agentopia.services.abi_service import get_abi
from agentopia.services.read_service import read
from agentopia.settings import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class PKManager(object):
    def __init__(self, pk):
        self._pk = pk

    @property
    def account(self):
        if self._pk:
            return Account.from_key(self._pk).address
        else:
            raise ValueError("pk not set")

    @property
    def pk(self):
        if self._pk:
            return self._pk
        else:
            raise ValueError("pk not set")

    def set(self, pk):
        self._pk = pk

    def __str__(self):
        return f"account: {self.account}, pk: {self.pk}"


pk_manager = PKManager(settings.AGENTOPIA_USER_PRIVATE_KEY)


class Contract(object):
    def __init__(
        self,
        contract_address: str,
        abi_path: str,
    ):
        self.contract_address = self.get_checksum_address(contract_address)
        self.abi_path = abi_path
        self.abi = get_abi(abi_path)
        self.mappings: Dict[str, str] = {}
        self.on_block_mappings: List[str] = []
        self.events_to_scan = None
        self.pk_manager = pk_manager

    @property
    def address(self):
        return self.contract_address

    @property
    def web3(self):
        provider = HTTPProvider(
            settings.RPC,
            request_kwargs={"timeout": 10},
        )

        web3 = Web3(provider)
        # web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        return web3

    @property
    def contract_instance(self):
        return self.web3.eth.contract(address=self.contract_address, abi=self.abi)

    def get_checksum_address(self, address):
        try:
            checksum_address = Web3.to_checksum_address(address)
        except ValueError:
            logger.exception(f"{address} is not valid")
        return checksum_address

    def decode_txn(self, data):
        data = dict(
            data
            | dedup(lambda x: (x["transactionHash"], x["logIndex"]))
            | select(lambda x: self.decode_log(event_name=None, logs=x))
            | where(lambda x: x != None)
            | groupby(lambda x: x["event_name"])
            | select(lambda x: (x[0], list(x[1] | select(lambda x: x["args"]))))
        )
        logger.debug(f"Found {len(data)} events!")
        return data

    def decode_log(self, event_name, logs):
        try:
            """
            eg. event = {
                "event_name": event_name,
                "timestamp": block_when,
                "log_index": log_index,
                "transaction_index": transaction_index,
                "txhash": txhash,
                "block_number": block_number,
                "address": event.address,
                "args": event["args"]
            }
            """
            data = dict(logs)
            data["topics"] = list(data["topics"] | where(lambda x: x != None))
            data["topics"] = list(map(HexBytes, data["topics"]))

            if not event_name:
                event_name = self.get_event_name_for_topic(data["topics"][0])

            data["transactionHash"] = HexBytes(data["transactionHash"])
            data["blockHash"] = data["transactionHash"]
            decoded_event = dict(
                get_event_data(self.web3.codec, self.get_event_abi(event_name), data)  # type: ignore
            )  # type: ignore

            decoded_event["log_index"] = decoded_event.pop("logIndex")  # type: ignore
            decoded_event["transaction_index"] = decoded_event.pop("transactionIndex")  # type: ignore
            decoded_event["txhash"] = decoded_event.pop("transactionHash")  # type: ignore
            decoded_event["event_name"] = decoded_event.pop("event")  # type: ignore
            return decoded_event
        except Exception:
            return None

    def _get_nonce(self):
        nonce = self.web3.eth.get_transaction_count(self.pk_manager.account)
        print(f"Nonce: {nonce}")
        return nonce

    def get_gas_price(self):
        self.web3.eth.set_gas_price_strategy(fast_gas_price_strategy)
        return int(self.web3.eth.generate_gas_price())  # type: ignore

    def write(self, function_name: str, *args, value=0):
        print(
            f"Writing {function_name} with args:{args} and value:{value} on {self.contract_address}:{settings.CHAIN_ID}"
        )
        try:
            return self.publish_txn(
                getattr(self.contract_instance.functions, function_name)(*args),
                value,
            )
        except ValueError as e:
            if "replacement transaction underpriced" in str(e):
                logger.info(f"Txn already underway for {(function_name, args, value)}")
            if "already known" in str(e):
                # the txn is already in the mempool so we need to speed up the txn
                logger.info(
                    "the txn is already in the mempool so we need to speed up the txn"
                )
                actual_gas_price = self.get_gas_price()
                logger.info(f"Trying with gas price {actual_gas_price}")
                return self.publish_txn(
                    getattr(self.contract_instance.functions, function_name)(*args),
                    value,
                    gas_price=actual_gas_price,
                )
            else:
                raise e

    def f(self, function_name, *args):
        return getattr(self.contract_instance.functions, function_name)(*args)

    def s(self, function_name, *args):
        return [self.contract_address, self.abi, function_name, *args]

    def publish_txn(self, transfer_txn, value, gas_price=None):
        nonce = self._get_nonce()

        transfer_txn = transfer_txn.build_transaction(
            {
                "from": self.pk_manager.account,
                "chainId": settings.CHAIN_ID,
                "nonce": nonce,
                "value": int(value),
                "gas": 10_000_000,
            }
        )

        signed_txn = self.web3.eth.account.sign_transaction(
            transfer_txn, private_key=self.pk_manager.pk
        )

        try:
            print(f"Sending raw transaction: {Web3.to_hex(signed_txn.raw_transaction)}")
            self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        except ValueError as e:
            error_message = str(e)
            if "nonce too low" in error_message:
                logger.warning(
                    f"nonce too low: {settings.CHAIN_ID}-{self.pk_manager.account}. Skipping for now"
                )
            elif (
                "replacement transaction underpriced" in error_message
                or "already known" in error_message
            ):
                logger.warning(
                    f"Txn {settings.CHAIN_ID}:{ Web3.to_hex(signed_txn.hash)} still in progress"
                )
            else:
                logger.exception(f"Write call failing for {settings.CHAIN_ID}")
        except requests.HTTPError as e:
            if "Too Many Requests" in str(e):
                raise e
            else:
                raise e
        except:
            logger.exception(f"Write call failing for {settings.CHAIN_ID}")

        txn_hash = self.web3.to_hex(Web3.keccak(signed_txn.raw_transaction))
        txn_receipt = self.web3.eth.wait_for_transaction_receipt(txn_hash)
        logger.info(f"View txn at {settings.CHAIN_EXPLORER}/tx/{txn_hash}")
        logger.info("txn_receipt ", txn_receipt)

        if txn_receipt["status"] == 0:  # Transaction failed
            logger.info("Transaction Status: Failed")
            error_data = txn_receipt["logs"]
            if error_data:
                for log in error_data:
                    logger.info(f"Log Data: {log['data']}")
                    try:
                        error_signature = log["topics"][0].hex()
                        error_abi = self.get_abi_for_topic(error_signature)
                        if error_abi:
                            decoded_error = self.web3.codec.decode_abi(
                                [
                                    input["type"]
                                    for input in error_abi.get("inputs", [])
                                ],
                                bytes.fromhex(log["data"][2:]),
                            )
                            logger.info(
                                f"Decoded Error ({error_abi.get('name')}): {decoded_error}"
                            )
                    except Exception as e:
                        logger.info(f"Error decoding custom error: {e}")

        new_nonce = self._get_nonce()
        logger.info(f"New nonce: {new_nonce}, old nonce: {nonce}")
        start_time = int(time.time())
        while new_nonce == nonce:
            logger.info(f"Waiting for confirmation: {txn_hash}")
            if (int(time.time()) - start_time) > 60 * 2:
                logger.info("Confirmation taking too long, leaving this for now...")
                break
            time.sleep(2)
            new_nonce = self._get_nonce()

        all_events = list(self.contract_instance.events.__dict__.keys())[2:]
        all_logs = defaultdict(list)
        for event in all_events:
            event_obj = getattr(self.contract_instance.events, event)
            if callable(event_obj):
                logs = event_obj().process_receipt(txn_receipt, errors=IGNORE)
                for log in logs:
                    if "errors" not in log:
                        logs = dict(log)
                        logs["args"] = dict(log["args"])
                        all_logs[event].append(logs)

        txn_receipt = dict(txn_receipt)
        txn_receipt["logs"] = all_logs
        return txn_receipt

    def read(
        self, function_name: str, *args, default_block="latest", caller_address=None
    ):
        return read(
            self.contract_address,
            self.abi,
            function_name,
            default_block,
            caller_address,
            args,
        )

    def get_event_name_for_topic(self, topic0):
        if not hasattr(self, "topic_to_event_name_mapping"):
            self.topic_to_event_name_mapping = dict(
                list(
                    self.get_all_event_names()
                    | select(
                        lambda event_name: (self.get_topic(event_name), event_name)
                    )
                )
            )
        try:
            if isinstance(topic0, HexBytes):
                topic0 = topic0.hex()
            return self.topic_to_event_name_mapping[topic0]
        except:
            event_abi = self.get_abi_for_topic(topic0)
            return event_abi.get("name")

    def get_abi_for_topic(self, topic0):
        if isinstance(topic0, HexBytes):
            topic0 = topic0.hex()
        if hasattr(self, "topic_to_abi_mapping"):
            return self.topic_to_abi_mapping[topic0]

        self.topic_to_abi_mapping = dict(
            list(
                self.get_all_event_names()
                | select(
                    lambda event_name: (
                        self.get_topic(event_name),
                        self.get_event_abi(event_name),
                    )
                )
            )
        )
        return self.topic_to_abi_mapping.get(topic0, {})

    def get_all_event_types(self):
        return list(
            self.get_all_event_names()
            | select(
                lambda event_name: getattr(self.contract_instance.events, event_name)
            )
        )

    def get_all_event_names(self):
        return list(
            self.contract_instance.abi
            | where(lambda x: x["type"] == "event")
            | select(lambda x: x["name"])
        )

    def get_event_abi(self, event_name):
        var_name = "__var_event_abi"
        if hasattr(self, var_name):
            if event_name in getattr(self, var_name):
                return getattr(self, var_name)[event_name]
        else:
            setattr(self, var_name, {})

        data = list(
            filter(lambda x: x.get("name") == event_name, self.contract_instance.abi)
        )
        if data:
            data = data[0]
        else:
            logger.exception("Invalid Event Name")

        getattr(self, var_name)[event_name] = data
        return data

    def get_topic(self, event_name):
        var_name = "__var_get_topic"
        if hasattr(self, var_name):
            if event_name in getattr(self, var_name):
                return getattr(self, var_name)[event_name]
        else:
            setattr(self, var_name, {})

        data = self.get_event_abi(event_name)
        input_types = list(data["inputs"] | select(lambda x: x["type"]))
        input_type_string = ",".join(input_types)
        message = f"{data['name']}({input_type_string})"

        k = keccak.new(digest_bits=256)
        k.update(message.encode("utf-8"))

        _topic = f"0x{k.hexdigest()}"

        getattr(self, var_name)[event_name] = _topic
        return _topic

    def __str__(self):
        return f"{self.contract_address} with {self.abi_path}"

    def __repr__(self):
        return f"{self.contract_address} with {self.abi_path}"

    def json(self):
        fields = [
            "contract_address",
            "abi_path",
            "mappings",
            "on_block_mappings",
            "index",
            "event_scan",
        ]
        return {field: self.__dict__[field] for field in fields}


def get_contract_instance(**kwargs):
    contract_instance = Contract(
        contract_address=kwargs["contract_address"],
        abi_path=kwargs["abi_path"],
    )

    return contract_instance
