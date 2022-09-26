# encoding: utf-8

import logging
from time import sleep
from agent.utils import convert_int
from agent.ckb_indexer import CKBIndexer, token_dict
from agent.ckb_rpc import CkbRpc
from agent.godwoken_rpc import GodwokenRpc
from agent.gw_config import devnet_config, testnet_config, \
    testnet_v1_1_config, mainnet_config, mainnet_v1_config
from agent.sched_custodian import get_custodian
import prometheus_client
from prometheus_client.core import CollectorRegistry, Gauge
from flask import Response, Flask
import os
import threading

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
Ping = None
LastBlockHash = None
LastBlockTimestamp = None
BlockTimeDifference = None
TPS = None
CommitTransacionCount = {}
CustodianStats = None
DepositDict = {}
WithdrawalDict = {}

TaskLock = threading.Lock()

def get_gw_stat_by_lock(lock_name, gw_rpc: GodwokenRpc, block_hash,
                        ckb_rpc: CkbRpc, gw_config):
    lock_type_hash = gw_config.get_lock_type_hash(lock_name)
    res = gw_rpc.gw_get_block_committed_info(block_hash)
    if res is None or res is None:
        raise Exception(f"Block hash: {block_hash} isn't committed.")
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


"""
Update metrics in batch. Some metrics are cumulative.
"""
def update_metrics(tip_number, ping, last_block_hash: str,
                   last_block_ts: int,
                   block_time_diff: int,
                   tps,
                   tx_cnt: int,
                   deposit, withdrawal):
    with TaskLock:
        global BlockNumber
        global Ping
        global LastBlockHash
        global LastBlockTimestamp
        global BlockTimeDifference
        global TPS
        global CommitTransacionCount
        global DepositDict
        global WithdrawalDict

        Ping = ping
        LastBlockHash = last_block_hash
        LastBlockTimestamp = last_block_ts
        BlockTimeDifference = block_time_diff
        TPS = tps
        CommitTransacionCount[BlockNumber] = tx_cnt
        DepositDict[BlockNumber] = deposit
        WithdrawalDict[BlockNumber] = withdrawal
        BlockNumber = tip_number # increase tip in the end


"""
Reset metrics after being scraped by grafana successfully.
"""
def reset_metrics():
    with TaskLock:
        global BlockNumber
        global CommitTransacionCount
        global DepositDict
        global WithdrawalDict
        if BlockNumber is not None:
            last_block_num = BlockNumber - 1
            for k in list(CommitTransacionCount.keys()):
                if k <= last_block_num:
                    CommitTransacionCount.pop(k, None)
            for k in list(DepositDict.keys()):
                if k <= last_block_num:
                    DepositDict.pop(last_block_num, None)
            for k in list(WithdrawalDict.keys()):
                if k <= last_block_num:
                    WithdrawalDict.pop(last_block_num, None)
            logging.info(f"Reset metrics for blocks before: {last_block_num}")

"""
General metrics job.
"""
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

        while True:
            sleep(1)
            logging.debug("Start running")
            if BlockNumber is None:
                try:
                    tip_number = self.gw_rpc.get_tip_number()
                    BlockNumber = tip_number
                except:
                    logging.exception("Cannot get tip number")
                    continue
            else:
                tip_number = BlockNumber

            try:
                ping = self.gw_rpc.ping()

                block = self.gw_rpc.get_block_by_number(hex(tip_number))
                if block is None:
                    continue
                last_block_hash = block['hash']
                last_block_ts = convert_int(block['raw']['timestamp'])
                tx_cnt = len(block['transactions'])

                previous_block_hash = block['raw']['parent_block_hash']
                previous_block = self.gw_rpc.get_block(previous_block_hash)
                previous_block_time = convert_int(previous_block['block']['raw']['timestamp'])
                block_time_diff = abs(last_block_ts - previous_block_time)

                if block_time_diff == 0:
                    tps = 0
                else:
                    tps = tx_cnt / block_time_diff * 1000
            except:
                logging.exception("get block info failed")
                continue
            try:
                deposit = get_gw_stat_by_lock(
                    "deposit_lock", self.gw_rpc,
                    last_block_hash, self.ckb_rpc,
                    self.gw_config)
            except:
                logging.exception("Failed to get deposit stats")
                continue
            try:
                withdrawal = get_gw_stat_by_lock(
                    "withdrawal_lock", self.gw_rpc,
                    last_block_hash, self.ckb_rpc,
                    self.gw_config)
            except:
                logging.exception("Failed to get withdrawal stats")
                continue
            update_metrics(
                    tip_number+1,
                    ping,
                    last_block_hash,
                    last_block_ts,
                    block_time_diff,
                    tps,
                    tx_cnt,
                    deposit,
                    withdrawal)


"""
It takes a lot more time to calculate Custodian metrics than others.
And custodian metrics don't need to be real-time level.
So put this in a slower thread.
"""
class CustodianJobThread(JobThread):
    def __init__(self):
        super().__init__()
    
    def run(self):
        global CustodianStats
        while True:
            sleep(10)
            try:
                CustodianStats = get_custodian(
                    self.ckb_indexer_url, self.gw_config,
                    BlockNumber)
            except:
                logging.exception("Failed to get custodian stats")


job = JobThread()
job.start()

custodian_job = CustodianJobThread()
custodian_job.start()

@NodeFlask.route("/metrics/godwoken/<block_number>")
@NodeFlask.route(
    "/metrics/godwoken",
    defaults={"block_number": None},
)
def exporter(block_number=None):
    global BlockNumber
    if block_number is not None:
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

    last_block_number.labels(gw_rpc_url=gw_rpc_url).set(BlockNumber)

    node_gw_ping.labels(gw_rpc_url=gw_rpc_url,
                        gw_ping=Ping).set(1)

    node_LastBlockInfo.labels(
        gw_rpc_url=gw_rpc_url,
        last_block_hash=LastBlockHash,
        last_blocknumber=BlockNumber,
        last_block_timestamp=LastBlockTimestamp,
    ).set(BlockTimeDifference)

    node_BlockDetail_transactions.labels(
        gw_rpc_url=gw_rpc_url).set(sum(CommitTransacionCount.values()))

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

    deposit_cnt = 0
    deposit_capacity = 0
    for _, (cnt, capacity) in DepositDict.items():
        deposit_cnt += cnt
        deposit_capacity += capacity
    withdrawal_cnt = 0
    withdrawal_capacity = 0
    for _, (cnt, capacity) in WithdrawalDict.items():
        withdrawal_cnt += cnt
        withdrawal_capacity += capacity
    one_ckb = 100_000_000
    deposit_capacity = deposit_capacity / one_ckb
    withdrawal_capacity = withdrawal_capacity / one_ckb

    gw_deposit_cnt.labels(gw_rpc_url=gw_rpc_url).set(deposit_cnt)
    gw_deposit_capacity.labels(gw_rpc_url=gw_rpc_url).set(deposit_capacity)
    gw_withdrawal_cnt.labels(gw_rpc_url=gw_rpc_url).set(withdrawal_cnt)
    gw_withdrawal_capacity.labels(gw_rpc_url=gw_rpc_url).set(withdrawal_capacity)

    reset_metrics()
    return Response(prometheus_client.generate_latest(registry),
                    mimetype="text/plain")
