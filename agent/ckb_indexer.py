from dataclasses import dataclass
from typing import Dict

import requests
import traceback

from agent.utils import convert_int
from agent.gw_config import GwConfig

token_dict: Dict = {
    "5c4ac961a2428137f27271cf2af205e5c55156d26d9ac285ed3170e8c4cc1501": {
        "name": "USDC",
        "decimals": 6,
    },
    "1b89ae72b96c4f02fa7667ab46febcedf9b495737752176303ddd215d66a615a": {
        "name": "USDT",
        "decimals": 6,
    },
    "08430183dda1cbd81912c4762a3006a59e2291d5bd43b48bb7fa7544cace9e4a": {
        "name": "TAI",
        "decimals": 8,
    },
    "9657b32fcdc463e13ec9205914fd91c443822a949937ae94add9869e7f2e1de8": {
        "name": "ETH",
        "decimals": 18,
    },
    "e5451c05231e1df43e4b199b5d12dbed820dfbea2769943bb593f874526eeb55": {
        "name": "dCKB",
        "decimals": 8,
    },
}


@dataclass()
class SudtStats:
    token: str
    args: str
    decimals: int
    total_amount: int = 0
    finalized_amount: int = 0
    count: int = 0


@dataclass()
class CustodianStats:
    sudt_stats: Dict
    capacity: int = 0
    finalized_capacity: int = 0
    cell_count: int = 0
    ckb_cell_count: int = 0


class CKBIndexer(object):
    def __init__(self, url):
        self.url = url

    def get_cells(self, code_hash, args, limit, cursor):
        limit = hex(limit)
        headers = {"Content-Type": "application/json"}
        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "get_cells",
            "params": [
                {
                    "script": {
                        "code_hash": code_hash,
                        "hash_type": "type",
                        "args": args,
                    },
                    "script_type": "lock",
                },
                "desc",
                limit,
            ],
        }
        if cursor is not None:
            payload["params"].append(cursor)
        try:
            r = requests.post(url="%s" % (self.url), json=payload, headers=headers)

            return r.json()
        except Exception:
            print(traceback.format_exc())

            return {"result": "-1"}

    def get_custodian_stats(
        self, gw_config: GwConfig, last_finalized_block_numbrer
    ) -> CustodianStats:
        custodian_script_type_hash = gw_config.get_lock_type_hash("custodian_lock")
        rollup_type_hash = gw_config.get_rollup_type_hash()
        capacity = 0
        finalized_capacity = 0
        cell_count = 0
        ckb_cell_count = 0
        cursor = None
        sudt_stats = init_custodian()
        limit = 1000
        while True:
            try:
                res = self.get_cells(
                    custodian_script_type_hash, rollup_type_hash, limit, cursor
                )
            except:
                print("get_cells failed: {}".format(traceback.format_exc()))
                continue
            result = res["result"]
            if result == "-1":
                continue
            cell_count += len(result["objects"])
            for cell in result["objects"]:
                c = convert_int(cell["output"]["capacity"])
                capacity += c

                args = cell["output"]["lock"]["args"]
                block_number = get_deposit_block_number_from_args(args)
                is_finalized = block_number <= last_finalized_block_numbrer
                if is_finalized:
                    finalized_capacity += c

                cell_output_type = cell["output"]["type"]
                output_data = cell["output_data"]
                if cell_output_type:
                    amount = output_data_to_int(output_data)
                    args = cell_output_type["args"].lstrip("0x")
                    if args in sudt_stats:
                        sudt = sudt_stats[args]
                        base = 10 ** sudt.decimals
                        true_amount = amount / base
                        sudt.total_amount += true_amount
                        sudt.count += 1
                        if is_finalized:
                            sudt.finalized_amount += true_amount
                        print(sudt)
                else:
                    ckb_cell_count += 1

            cursor = result["last_cursor"]
            if cursor == "0x":
                break
        custodian_stats = CustodianStats(
            sudt_stats, capacity, finalized_capacity, cell_count, ckb_cell_count
        )
        return custodian_stats


## parse mol format
def get_deposit_block_number_from_args(args: str):
    if args.startswith("0x"):
        args = args[2:]
    args = bytes.fromhex(args)
    args = args[32:]
    start = int.from_bytes(args[12:16], byteorder="little", signed=False)
    return int.from_bytes(args[start:], byteorder="little", signed=False)


def output_data_to_int(s: str, byteorder="little", signed=False):
    try:
        s = s.lstrip("0x")
        s = s[:16]
        byte_arr = bytes.fromhex(s)
        return int.from_bytes(byte_arr, byteorder=byteorder, signed=signed)
    except:
        print("convert hex: {} to int Error: {}".format(s, traceback.format_exc()))
        return 0


def init_custodian(token_dict: Dict = token_dict) -> Dict[str, SudtStats]:
    res = {}
    for args, detail in token_dict.items():
        res[args] = SudtStats(
            token=detail["name"], args=args, decimals=detail["decimals"]
        )
    return res
