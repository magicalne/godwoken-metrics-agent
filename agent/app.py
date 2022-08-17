# encoding: utf-8

import logging
import requests
from time import sleep
from agent.utils import convert_int
from agent.ckb_indexer import CKBIndexer, token_dict
from agent.ckb_rpc import CkbRpc
from agent.godwoken_rpc import GodwokenRpc
from agent.gw_config import GwConfig, devnet_config, testnet_config, \
    testnet_v1_1_config, mainnet_config, mainnet_v1_config
import prometheus_client
from prometheus_client.core import CollectorRegistry, Gauge, Info
from flask import Response, Flask
import os
import threading

from agent.sched_custodian import get_custodian
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

DISABLE_CUSTODIAN_STATS = 'DISABLE_CUSTODIAN_STATS'
NodeFlask = Flask(__name__)
gw_rpc_url = os.environ["GW_RPC_URL"]
ckb_indexer_url = os.environ["CKB_INDEXER_URL"]
ckb_rpc_url = os.environ["CKB_RPC_URL"]
net_env = os.environ["NET_ENV"]
logging.info(f"net_env: {net_env}")

BlockNumber = None
## GLOBAL METRICS
LastBlockNumber = None
Ping = None
LastBlockHash = None
LastBlockTimestamp = None
BlockTimeDifference = None
TPS = None
CommitTransacionCount = None
CustodianStats = None
DepositCount = 0
DepositCapacity = 0
WithdrawalCount = 0
WithdrawalCapacity = 0


def get_gw_stat_by_lock(lock_name, gw_rpc: GodwokenRpc, block_hash,
                        ckb_rpc: CkbRpc, gw_config):
    lock_type_hash = gw_config.get_lock_type_hash(lock_name)
    res = gw_rpc.gw_get_block_committed_info(block_hash)
    if res is None or res is None:
        return (0, 0)
    tx = res["transaction_hash"]
    res = ckb_rpc.get_transaction(tx)
    inputs = res["transaction"]["inputs"]
    output_dict = {}
    if inputs is None or len(inputs) == 0:
        return (0, 0)
    try:
        for i in inputs:
            tx_hash = i["previous_output"]["tx_hash"]
            res = ckb_rpc.get_transaction(tx_hash)
            outputs = res["transaction"]["outputs"]
            for o in outputs:
                code_hash = o["lock"]["code_hash"]
                if code_hash == lock_type_hash:
                    amount = convert_int(o["capacity"])
                    output_dict[o["lock"]["args"]] = amount
        return (len(output_dict), sum(output_dict.values()))
    except:
        logging.error("Error get stat by lock: %s",
                      lock_type_hash,
                      exc_info=True)
        return (len(output_dict), sum(output_dict.values()))


class JobThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        global gw_rpc_url
        global ckb_indexer_url
        global ckb_rpc_url
        global net_env

        self.gw_rpc = GodwokenRpc(gw_rpc_url)
        self.ckb_indexer_url = ckb_indexer_url
        self.ckb_indexer = CKBIndexer(ckb_indexer_url)
        self.ckb_rpc = CkbRpc(ckb_rpc_url)
        if net_env is None:
            logging.info("net_env is None, use testnet config")
            self.gw_config = testnet_config()
        else:
            net_env = net_env.lower()
            if net_env == "mainnet":
                self.gw_config = mainnet_config()
            elif net_env == "testnet":
                self.gw_config = testnet_config()
            elif net_env == "testnet_v1_1":
                self.gw_config = testnet_v1_1_config()
            elif net_env == "mainnet_v1":
                self.gw_config = mainnet_v1_config()
            else:
                logging.info("use devnet")
                rollup_result_path = os.environ["ROLLUP_RESULT_PATH"]
                scripts_result_path = os.environ["SCRIPTS_RESULT_PATH"]
                self.gw_config = devnet_config(rollup_result_path,
                                               scripts_result_path)
                if self.gw_config == -1:
                    logging.info(
                        "the env var: [ROLLUP_RESULT_PATH] and [SCRIPTS_RESULT_PATH] are not found, use testnet"
                    )
                    self.gw_config = testnet_config()

    def run(self):
        global BlockNumber
        global LastBlockNumber
        global Ping
        ## remove Web3Version
        ##global Web3Version
        global LastBlockHash
        global LastBlockTimestamp
        global BlockTimeDifference
        global TPS
        global CommitTransacionCount
        global CustodianStats
        global DepositCount
        global DepositCapacity
        global WithdrawalCount
        global WithdrawalCapacity

        while True:
            sleep(5)
            logging.info("Start running")
            if BlockNumber is None:
                try:
                    LastBlockNumber = self.gw_rpc.get_tip_number()
                except:
                    logging.exception("Cannot get tip number")
                    continue
            else:
                LastBlockNumber = BlockNumber

            try:
                Ping = self.gw_rpc.ping()

                block = self.gw_rpc.get_block_by_number(hex(LastBlockNumber))
                LastBlockHash = block['hash']
                LastBlockTimestamp = convert_int(block['raw']['timestamp'])
                CommitTransacionCount = len(block['transactions'])

                previous_block_hash = block['raw']['parent_block_hash']
                previous_block = self.gw_rpc.get_block(previous_block_hash)
                previous_block_time = convert_int(previous_block['block']['raw']['timestamp'])
                BlockTimeDifference = abs(LastBlockTimestamp - previous_block_time)

                TPS = CommitTransacionCount / BlockTimeDifference * 1000
            except Exception as e:
                ## ignore any exception
                logging.error("get block info failed", exc_info=e)
                continue
            one_ckb = 100_000_000
            if DISABLE_CUSTODIAN_STATS not in os.environ:
                logging.info("Loading custodian stats")
                try:
                    CustodianStats = get_custodian(
                        self.ckb_indexer_url, self.gw_config,
                        LastBlockNumber)
                except:
                    logging.exception("Failed to get custodian stats")
            logging.info("Loading deposit stats")
            try:
                DepositCount, DepositCapacity = get_gw_stat_by_lock(
                    "deposit_lock", self.gw_rpc,
                    LastBlockHash, self.ckb_rpc,
                    self.gw_config)
                DepositCapacity = DepositCapacity / one_ckb
            except:
                logging.exception("Failed to get deposit stats")
            logging.info("Loading withdrawal stats")
            try:
                WithdrawalCount, WithdrawalCapacity = get_gw_stat_by_lock(
                    "withdrawal_lock", self.gw_rpc,
                    LastBlockHash, self.ckb_rpc,
                    self.gw_config)
                WithdrawalCapacity = WithdrawalCapacity / one_ckb
            except:
                logging.exception("Failed to get withdrawal stats")


job = JobThread()
job.start()


@NodeFlask.route("/metrics/godwoken/<block_number>")
@NodeFlask.route(
    "/metrics/godwoken",
    defaults={"block_number": None},
)
def exporter(block_number=None):
    global BlockNumber
    BlockNumber = block_number
    registry = CollectorRegistry(auto_describe=False)

    last_block_number = Gauge("Node_Get_LastBlockNumber",
                              "LAST_BLOCK_NUMBER", ["gw_rpc_url"],
                              registry=registry)

    node_gw_ping = Gauge("Node_Get_Gw_Ping",
                         "Node_GW_PING", ["gw_rpc_url", "gw_ping"],
                         registry=registry)

    node_LastBlockInfo = Gauge(
        "Node_Get_LastBlockInfo",
        "Get LastBlockInfo, label include last_block_hash, last_blocknumber. value is last_block_timestamp;",
        [
            "gw_rpc_url", "last_block_hash", "last_blocknumber",
            "last_block_timestamp"
        ],
        registry=registry,
    )

    node_BlockDetail_transactions = Gauge(
        "Node_Get_BlockDetail_transactions",
        "Get LastTxInfo, label include last_block_hash, tx_hash. value is proposal_transactions in block;",
        ["gw_rpc_url"],
        registry=registry,
    )

    node_BlockTimeDifference = Gauge(
        "Node_Get_BlockTimeDifference",
        "Get current block time and previous block time,value is Calculate the difference into seconds;",
        ["gw_rpc_url"],
        registry=registry,
    )

    # Too slow, fix it later.
    gw_custodian_capacity = Gauge(
        "Node_Get_CustodianCapacity",
        "Get custodian ckb capacity from ckb indexer",
        ["gw_rpc_url"],
        registry=registry,
    )

    gw_custodian_finalized_capacity = Gauge(
        "Node_Get_CustodianFinalizedCapacity",
        "Get custodian finalized ckb capacity from ckb indexer",
        ["gw_rpc_url"],
        registry=registry,
    )

    gw_custodian_cell_count = Gauge(
        "Node_Get_CustodianCellCount",
        "Get custodian cell count from ckb indexer",
        ["gw_rpc_url"],
        registry=registry,
    )

    gw_custodian_ckb_cell_count = Gauge(
        "Node_Get_CustodianCkbCellCount",
        "Get custodian ckb cell count from ckb indexer",
        ["gw_rpc_url"],
        registry=registry,
    )

    sudt_guage_dict = {
        k: {
            "total_amount":
            Gauge(
                "Node_" + v["name"] + "_TotalAmount",
                "Get sudt: " + v["name"] + " total amount",
                ["gw_rpc_url"],
                registry=registry,
            ),
            "finalized_amount":
            Gauge(
                "Node_" + v["name"] + "_FinalizedAmount",
                "Get sudt: " + v["name"] + " finalized amount",
                ["gw_rpc_url"],
                registry=registry,
            ),
            "count":
            Gauge(
                "Node_" + v["name"] + "_Count",
                "Get sudt: " + v["name"] + " count",
                ["gw_rpc_url"],
                registry=registry,
            ),
        }
        for k, v in token_dict.items()
    }

    gw_deposit_cnt = Gauge(
        "Node_Get_DepositCnt",
        "Get deposit count from current block",
        ["gw_rpc_url"],
        registry=registry,
    )
    gw_deposit_capacity = Gauge(
        "Node_Get_DepositCapacity",
        "Get deposit capacity from current block",
        ["gw_rpc_url"],
        registry=registry,
    )
    gw_withdrawal_cnt = Gauge(
        "Node_Get_WithdrawalCnt",
        "Get withdrawal count from current block",
        ["gw_rpc_url"],
        registry=registry,
    )
    gw_withdrawal_capacity = Gauge(
        "Node_Get_WithdrawalCapacity",
        "Get withdrawal capacityfrom current block",
        ["gw_rpc_url"],
        registry=registry,
    )
    gw_tps = Gauge(
        "Node_TPS",
        "Get current TPS betweenn last 2 blocks",
        ["gw_rpc_url"],
        registry=registry,
    )

    global LastBlockNumber
    last_block_number.labels(gw_rpc_url=gw_rpc_url).set(LastBlockNumber)

    node_gw_ping.labels(gw_rpc_url=gw_rpc_url,
                        gw_ping=Ping).set(1)

    node_LastBlockInfo.labels(
        gw_rpc_url=gw_rpc_url,
        last_block_hash=LastBlockHash,
        last_blocknumber=LastBlockNumber,
        last_block_timestamp=LastBlockTimestamp,
    ).set(BlockTimeDifference)

    node_BlockDetail_transactions.labels(
        gw_rpc_url=gw_rpc_url).set(CommitTransacionCount)

    gw_tps.labels(gw_rpc_url=gw_rpc_url).set(TPS)

    node_BlockTimeDifference.labels(gw_rpc_url=gw_rpc_url).set(BlockTimeDifference)
    one_ckb = 100_000_000
    if CustodianStats:
        sudt_stats = CustodianStats.sudt_stats
        capacity = CustodianStats.capacity
        finalized_capacity = CustodianStats.finalized_capacity
        cell_count = CustodianStats.cell_count
        ckb_cell_count = CustodianStats.ckb_cell_count
        capacity = int(capacity / one_ckb)
        gw_custodian_capacity.labels(gw_rpc_url).set(capacity)
        finalized_capacity = int(finalized_capacity / one_ckb)
        gw_custodian_finalized_capacity.labels(gw_rpc_url).set(
            finalized_capacity)
        gw_custodian_cell_count.labels(gw_rpc_url).set(cell_count)
        gw_custodian_ckb_cell_count.labels(gw_rpc_url).set(ckb_cell_count)

        for args, stats in sudt_stats.items():
            base = 10**stats.decimals
            sudt_guage = sudt_guage_dict[args]
            total_amount_guage = sudt_guage["total_amount"]
            finalized_amount_guage = sudt_guage["finalized_amount"]
            count_guage = sudt_guage["count"]
            total_amount_guage.labels(gw_rpc_url).set(stats.total_amount / base)
            finalized_amount_guage.labels(gw_rpc_url).set(
                stats.finalized_amount / base)
            count_guage.labels(gw_rpc_url).set(stats.count)

    gw_deposit_cnt.labels(gw_rpc_url=gw_rpc_url).set(DepositCount)
    gw_deposit_capacity.labels(gw_rpc_url=gw_rpc_url).set(DepositCapacity)
    gw_withdrawal_cnt.labels(gw_rpc_url=gw_rpc_url).set(WithdrawalCount)
    gw_withdrawal_capacity.labels(gw_rpc_url=gw_rpc_url).set(WithdrawalCapacity)

    return Response(prometheus_client.generate_latest(registry),
                    mimetype="text/plain")
