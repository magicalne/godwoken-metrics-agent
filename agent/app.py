# encoding: utf-8

import logging
import requests
from time import sleep
from agent.utils import convert_int
from agent.ckb_indexer import CKBIndexer, token_dict
from agent.ckb_rpc import CkbRpc
from agent.godwoken_rpc import GodwokenRpc
from agent.gw_config import GwConfig, devnet_config, testnet_config, mainnet_config
import prometheus_client
from prometheus_client.core import CollectorRegistry, Gauge, Info
from flask import Response, Flask
import os
import threading

from agent.sched_custodian import get_custodian

DISABLE_CUSTODIAN_STATS = 'DISABLE_CUSTODIAN_STATS'
NodeFlask = Flask(__name__)
web3_url = os.environ["WEB3_URL"]
gw_rpc_url = os.environ["GW_RPC_URL"]
ckb_indexer_url = os.environ["CKB_INDEXER_URL"]
ckb_rpc_url = os.environ["CKB_RPC_URL"]
net_env = os.environ["NET_ENV"]
logging.info(f"net_env: {net_env}")

BlockNumber = None
## GLOBAL METRICS
LastBlockNumber = None
Ping = None
Web3Version = None
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


class RpcGet(object):

    def __init__(self, web3_url):
        self.web3_url = web3_url

    def get_LastBlockHeight(self):
        headers = {"Content-Type": "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"eth_blockNumber", "params":[]}'
        try:
            r = requests.post(url="%s" % (self.web3_url),
                              data=data,
                              headers=headers)
            replay = r.json()["result"]
            return {"last_blocknumber": convert_int(replay)}
        except:
            logging.error("Error getting block height", exc_info=True)
            return {"last_blocknumber": "-1"}

    def get_LastBlockHash(self, block_number=None):
        if block_number is not None:
            block_hash = self.get_block_hash(block_number)["blocknumber_hash"]
            return {"last_block_hash": block_hash}
        headers = {"Content-Type": "application/json"}
        data = (
            '{"id":2, "jsonrpc":"2.0", "method":"gw_get_tip_block_hash", "params":[]}'
        )
        try:
            r = requests.post(url="%s" % (self.web3_url),
                              data=data,
                              headers=headers)
            replay = r.json()["result"]
            return {"last_block_hash": str(replay)}
        except:
            logging.error(
                "Error getting last block hash, block number: %d",
                block_number,
                exc_info=True,
            )
            return {"last_block_hash": "-1"}

    def get_BlockDetail(self, block_hash):
        headers = {"Content-Type": "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"gw_get_block", "params":["%s"]}' % (
            block_hash)
        try:
            r = requests.post(url="%s" % (self.web3_url),
                              data=data,
                              headers=headers)
            res = r.json()
            replay = res["result"]
            return {
                "blocknumber":
                convert_int(replay["block"]["raw"]["number"]),
                "parent_block_hash":
                replay["block"]["raw"]["parent_block_hash"],
                "commit_transactions":
                len(replay["block"]["transactions"]),
                "transactions":
                replay["block"]["transactions"],
                "blocknumber_timestamp":
                convert_int(replay["block"]["raw"]["timestamp"]),
            }
        except:
            logging.exception("Error get block detail, block hash: %s",
                              block_hash)
            return {
                "blocknumber": "-1",
                "parent_block_hash": "-1",
                "commit_transactions": "-1",
                "transactions": [],
                "blocknumber_timestamp": "-1",
            }

    def get_BlockDetailByNumber(self, number):
        headers = {"Content-Type": "application/json"}
        data = (
            '{"id":2, "jsonrpc":"2.0", "method":"gw_get_block_by_number", "params":["%s"]}'
            % (number))
        try:
            r = requests.post(url="%s" % (self.web3_url),
                              data=data,
                              headers=headers)
            replay = r.json()["result"]
            return {
                "blocknumber":
                convert_int(replay["block"]["raw"]["number"]),
                "commit_transactions":
                len(replay["block"]["transactions"]),
                "transactions":
                replay["block"]["transactions"],
                "blocknumber_timestamp":
                convert_int(replay["block"]["raw"]["timestamp"]),
            }
        except:
            logging.exception("Error get block detail by number: %d", number)
            return {
                "blocknumber": "-1",
                "commit_transactions": "-1",
                "transactions": [],
                "blocknumber_timestamp": "-1",
            }

    def get_block_hash(self, blocknumber):
        headers = {"Content-Type": "application/json"}
        if type(blocknumber) == int:
            blocknumber = hex(blocknumber)
        data = (
            '{"id":2, "jsonrpc":"2.0", "method":"gw_get_block_hash", "params":["%s"]}'
            % (blocknumber))
        try:
            r = requests.post(url="%s" % (self.web3_url),
                              data=data,
                              headers=headers)
            replay = r.json()["result"]
            return {"blocknumber_hash": str(replay)}
        except:
            logging.error("Error get block hash. block number: %d",
                          blocknumber)
            return {"blocknumber_hash": "-1"}

    def get_gw_ping(self):
        headers = {"Content-Type": "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"gw_ping", "params":[]}'
        try:
            r = requests.post(url="%s" % (self.web3_url),
                              data=data,
                              headers=headers)
            replay = r.json()["result"]
            return {"gw_ping_status": replay}
        except:
            return {"gw_ping_status": "-1"}

    def web3_clientVersion(self):
        headers = {"Content-Type": "application/json"}
        data = '{"id":1, "jsonrpc":"2.0", "method":"web3_clientVersion", "params":[]}'
        try:
            r = requests.post(url="%s" % (self.web3_url),
                              data=data,
                              headers=headers)
            replay = r.json()["result"]
            return {"web3_clientVersion": replay}
        except:
            return {"web3_clientVersion": "-1"}


def get_gw_stat_by_lock(lock_name, gw_rpc: GodwokenRpc, block_hash,
                        ckb_rpc: CkbRpc, gw_config):
    lock_type_hash = gw_config.get_lock_type_hash(lock_name)
    res = gw_rpc.gw_get_block_committed_info(block_hash)
    if res is None or res['result'] is None:
        return (0, 0)
    tx = res["result"]["transaction_hash"]
    res = ckb_rpc.get_transaction(tx)
    inputs = res["result"]["transaction"]["inputs"]
    output_dict = {}
    if inputs is None or len(inputs) == 0:
        return (0, 0)
    try:
        for i in inputs:
            tx_hash = i["previous_output"]["tx_hash"]
            res = ckb_rpc.get_transaction(tx_hash)
            outputs = res["result"]["transaction"]["outputs"]
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
        global web3_url
        global gw_rpc_url
        global ckb_indexer_url
        global ckb_rpc_url
        global net_env

        self.get_result = RpcGet(web3_url)
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
        global Web3Version
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
            logging.info("Start running")
            if BlockNumber is None:
                LastBlockNumber = self.gw_rpc.get_tip_number()
            else:
                LastBlockNumber = BlockNumber

            Ping = self.get_result.get_gw_ping()
            Web3Version = self.get_result.web3_clientVersion()

            LastBlockHash = self.get_result.get_LastBlockHash(
                block_number=LastBlockNumber)

            LastBlockDetail = self.get_result.get_BlockDetail(
                LastBlockHash["last_block_hash"])
            if "-1" in LastBlockDetail.values():
                print(LastBlockDetail)
            else:
                PreviousBlock_hash = self.get_result.get_block_hash(
                    hex((LastBlockDetail["blocknumber"]) - 1))
                PreviousBlockDetail = self.get_result.get_BlockDetail(
                    PreviousBlock_hash["blocknumber_hash"])
                LastBlock_Time = convert_int(
                    LastBlockDetail["blocknumber_timestamp"])
                LastBlockTimestamp = LastBlock_Time
                PreviousBlock_Time = convert_int(
                    PreviousBlockDetail["blocknumber_timestamp"])
                BlockTimeDifference = abs(LastBlock_Time - PreviousBlock_Time)
                CommitTransacionCount = LastBlockDetail["commit_transactions"]
                TPS = LastBlockDetail[
                    "commit_transactions"] / BlockTimeDifference * 1000
            one_ckb = 100_000_000
            if DISABLE_CUSTODIAN_STATS not in os.environ:
                logging.info("Loading custodian stats")
                try:
                    CustodianStats = get_custodian(
                        self.ckb_indexer_url, self.gw_config,
                        LastBlockDetail["blocknumber"])
                except:
                    logging.exception("Failed to get custodian stats")
            logging.info("Loading deposit stats")
            try:
                DepositCount, DepositCapacity = get_gw_stat_by_lock(
                    "deposit_lock", self.gw_rpc,
                    LastBlockHash["last_block_hash"], self.ckb_rpc,
                    self.gw_config)
                DepositCapacity = DepositCapacity / one_ckb
            except:
                logging.exception("Failed to get deposit stats")
            logging.info("Loading withdrawal stats")
            try:
                WithdrawalCount, WithdrawalCapacity = get_gw_stat_by_lock(
                    "withdrawal_lock", self.gw_rpc,
                    LastBlockHash["last_block_hash"], self.ckb_rpc,
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
                              "LAST_BLOCK_NUMBER", ["web3_url"],
                              registry=registry)

    node_gw_ping = Gauge("Node_Get_Gw_Ping",
                         "Node_GW_PING", ["web3_url", "gw_ping"],
                         registry=registry)
    node_web3_clientVersion = Info(
        "Node_Get_Web3_ClientVersion",
        "Node_Web3_ClientVersion",
        ["web3_url"],
        registry=registry,
    )

    node_LastBlockInfo = Gauge(
        "Node_Get_LastBlockInfo",
        "Get LastBlockInfo, label include last_block_hash, last_blocknumber. value is last_block_timestamp;",
        [
            "web3_url", "last_block_hash", "last_blocknumber",
            "last_block_timestamp"
        ],
        registry=registry,
    )

    node_BlockDetail_transactions = Gauge(
        "Node_Get_BlockDetail_transactions",
        "Get LastTxInfo, label include last_block_hash, tx_hash. value is proposal_transactions in block;",
        ["web3_url"],
        registry=registry,
    )

    node_BlockTimeDifference = Gauge(
        "Node_Get_BlockTimeDifference",
        "Get current block time and previous block time,value is Calculate the difference into seconds;",
        ["web3_url"],
        registry=registry,
    )

    # Too slow, fix it later.
    gw_custodian_capacity = Gauge(
        "Node_Get_CustodianCapacity",
        "Get custodian ckb capacity from ckb indexer",
        ["web3_url"],
        registry=registry,
    )

    gw_custodian_finalized_capacity = Gauge(
        "Node_Get_CustodianFinalizedCapacity",
        "Get custodian finalized ckb capacity from ckb indexer",
        ["web3_url"],
        registry=registry,
    )

    gw_custodian_cell_count = Gauge(
        "Node_Get_CustodianCellCount",
        "Get custodian cell count from ckb indexer",
        ["web3_url"],
        registry=registry,
    )

    gw_custodian_ckb_cell_count = Gauge(
        "Node_Get_CustodianCkbCellCount",
        "Get custodian ckb cell count from ckb indexer",
        ["web3_url"],
        registry=registry,
    )

    sudt_guage_dict = {
        k: {
            "total_amount":
            Gauge(
                "Node_" + v["name"] + "_TotalAmount",
                "Get sudt: " + v["name"] + " total amount",
                ["web3_url"],
                registry=registry,
            ),
            "finalized_amount":
            Gauge(
                "Node_" + v["name"] + "_FinalizedAmount",
                "Get sudt: " + v["name"] + " finalized amount",
                ["web3_url"],
                registry=registry,
            ),
            "count":
            Gauge(
                "Node_" + v["name"] + "_Count",
                "Get sudt: " + v["name"] + " count",
                ["web3_url"],
                registry=registry,
            ),
        }
        for k, v in token_dict.items()
    }

    gw_deposit_cnt = Gauge(
        "Node_Get_DepositCnt",
        "Get deposit count from current block",
        ["web3_url"],
        registry=registry,
    )
    gw_deposit_capacity = Gauge(
        "Node_Get_DepositCapacity",
        "Get deposit capacity from current block",
        ["web3_url"],
        registry=registry,
    )
    gw_withdrawal_cnt = Gauge(
        "Node_Get_WithdrawalCnt",
        "Get withdrawal count from current block",
        ["web3_url"],
        registry=registry,
    )
    gw_withdrawal_capacity = Gauge(
        "Node_Get_WithdrawalCapacity",
        "Get withdrawal capacityfrom current block",
        ["web3_url"],
        registry=registry,
    )
    gw_tps = Gauge(
        "Node_TPS",
        "Get current TPS betweenn last 2 blocks",
        ["web3_url"],
        registry=registry,
    )

    last_block_number.labels(web3_url=web3_url).set(LastBlockNumber)

    node_gw_ping.labels(web3_url=web3_url,
                        gw_ping=Ping["gw_ping_status"]).set(1)

    node_web3_clientVersion.labels(web3_url=web3_url).info(Web3Version)

    node_LastBlockInfo.labels(
        web3_url=web3_url,
        last_block_hash=LastBlockHash,
        last_blocknumber=LastBlockNumber,
        last_block_timestamp=LastBlockTimestamp,
    ).set(BlockTimeDifference)

    node_BlockDetail_transactions.labels(
        web3_url=web3_url).set(CommitTransacionCount)

    gw_tps.labels(web3_url=web3_url).set(TPS)

    node_BlockTimeDifference.labels(web3_url=web3_url).set(BlockTimeDifference)
    one_ckb = 100_000_000
    if CustodianStats:
        sudt_stats = CustodianStats.sudt_stats
        capacity = CustodianStats.capacity
        finalized_capacity = CustodianStats.finalized_capacity
        cell_count = CustodianStats.cell_count
        ckb_cell_count = CustodianStats.ckb_cell_count
        capacity = int(capacity / one_ckb)
        gw_custodian_capacity.labels(web3_url).set(capacity)
        finalized_capacity = int(finalized_capacity / one_ckb)
        gw_custodian_finalized_capacity.labels(web3_url).set(
            finalized_capacity)
        gw_custodian_cell_count.labels(web3_url).set(cell_count)
        gw_custodian_ckb_cell_count.labels(web3_url).set(ckb_cell_count)

        for args, stats in sudt_stats.items():
            base = 10**stats.decimals
            sudt_guage = sudt_guage_dict[args]
            total_amount_guage = sudt_guage["total_amount"]
            finalized_amount_guage = sudt_guage["finalized_amount"]
            count_guage = sudt_guage["count"]
            total_amount_guage.labels(web3_url).set(stats.total_amount / base)
            finalized_amount_guage.labels(web3_url).set(
                stats.finalized_amount / base)
            count_guage.labels(web3_url).set(stats.count)

    gw_deposit_cnt.labels(web3_url=web3_url).set(DepositCount)
    gw_deposit_capacity.labels(web3_url=web3_url).set(DepositCapacity)
    gw_withdrawal_cnt.labels(web3_url=web3_url).set(WithdrawalCount)
    gw_withdrawal_capacity.labels(web3_url=web3_url).set(WithdrawalCapacity)

    return Response(prometheus_client.generate_latest(registry),
                    mimetype="text/plain")
