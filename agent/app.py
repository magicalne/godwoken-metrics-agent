# encoding: utf-8

import requests
from time import sleep
from agent.utils import convert_int
from agent.ckb_indexer import CKBIndexer, token_dict
from agent.ckb_rpc import CkbRpc
from agent.godwoken_rpc import GodwokenRpc
from agent.gw_config import GwConfig, devnet_config, testnet_config, mainnet_config
from agent.sched_custodian import SchedCustodian
import prometheus_client
from prometheus_client.core import CollectorRegistry, Gauge, Info
from flask import Response, Flask
import os

from agent.sched_cuustodian import get_custodian


NodeFlask = Flask(__name__)
web3_url = os.environ["WEB3_URL"]
gw_rpc_url = os.environ["GW_RPC_URL"]
ckb_indexer_url = os.environ["CKB_INDEXER_URL"]
ckb_rpc_url = os.environ["CKB_RPC_URL"]
net_env = os.environ["NET_ENV"]


class RpcGet(object):
    def __init__(self, web3_url):
        self.web3_url = web3_url

    def get_LastBlockHeight(self):
        headers = {"Content-Type": "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"eth_blockNumber", "params":[]}'
        try:
            r = requests.post(url="%s" % (self.web3_url), data=data, headers=headers)
            replay = r.json()["result"]
            return {"last_blocknumber": convert_int(replay)}
        except:
            return {"last_blocknumber": "-1"}

    def get_LastBlockHash(self):
        headers = {"Content-Type": "application/json"}
        data = (
            '{"id":2, "jsonrpc":"2.0", "method":"gw_get_tip_block_hash", "params":[]}'
        )
        try:
            r = requests.post(url="%s" % (self.web3_url), data=data, headers=headers)
            replay = r.json()["result"]
            return {"last_block_hash": str(replay)}
        except:
            return {"last_block_hash": "-1"}

    def get_BlockDetail(self, block_hash):
        headers = {"Content-Type": "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"gw_get_block", "params":["%s"]}' % (
            block_hash
        )
        try:
            r = requests.post(url="%s" % (self.web3_url), data=data, headers=headers)
            replay = r.json()["result"]
            return {
                "blocknumber": convert_int(replay["block"]["raw"]["number"]),
                "parent_block_hash": replay["block"]["raw"]["parent_block_hash"],
                "commit_transactions": len(replay["block"]["transactions"]),
                "transactions": replay["block"]["transactions"],
                "blocknumber_timestamp": convert_int(
                    replay["block"]["raw"]["timestamp"]
                ),
            }
        except:
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
            % (number)
        )
        try:
            r = requests.post(url="%s" % (self.web3_url), data=data, headers=headers)
            replay = r.json()["result"]
            return {
                "blocknumber": convert_int(replay["block"]["raw"]["number"]),
                "commit_transactions": len(replay["block"]["transactions"]),
                "transactions": replay["block"]["transactions"],
                "blocknumber_timestamp": convert_int(
                    replay["block"]["raw"]["timestamp"]
                ),
            }
        except:
            return {
                "blocknumber": "-1",
                "commit_transactions": "-1",
                "transactions": [],
                "blocknumber_timestamp": "-1",
            }

    def get_block_hash(self, blocknumber):
        headers = {"Content-Type": "application/json"}
        data = (
            '{"id":2, "jsonrpc":"2.0", "method":"gw_get_block_hash", "params":["%s"]}'
            % (blocknumber)
        )
        try:
            r = requests.post(url="%s" % (self.web3_url), data=data, headers=headers)
            replay = r.json()["result"]
            return {"blocknumber_hash": str(replay)}
        except:
            return {"blocknumber_hash": "-1"}

    def get_gw_ping(self):
        headers = {"Content-Type": "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"gw_ping", "params":[]}'
        try:
            r = requests.post(url="%s" % (self.web3_url), data=data, headers=headers)
            replay = r.json()["result"]
            return {"gw_ping_status": replay}
        except:
            return {"gw_ping_status": "-1"}

    def web3_clientVersion(self):
        headers = {"Content-Type": "application/json"}
        data = '{"id":1, "jsonrpc":"2.0", "method":"web3_clientVersion", "params":[]}'
        try:
            r = requests.post(url="%s" % (self.web3_url), data=data, headers=headers)
            replay = r.json()["result"]
            return {"web3_clientVersion": replay}
        except:
            return {"web3_clientVersion": "-1"}


def get_gw_stat_by_lock(lock_name, gw_rpc: GodwokenRpc, block_hash, ckb_rpc: CkbRpc):
    lock_type_hash = gw_config.get_lock_type_hash(lock_name)
    res = gw_rpc.gw_get_block_committed_info(block_hash)
    tx = res["result"]["transaction_hash"]
    res = ckb_rpc.get_transaction(tx)
    inputs = res["result"]["transaction"]["inputs"]
    cnt = 0
    amount = 0
    if inputs is None or len(inputs) == 0:
        return (cnt, amount)
    try:
        for i in inputs:
            tx_hash = i["previous_output"]["tx_hash"]
            res = ckb_rpc.get_transaction(tx_hash)
            outputs = res["result"]["transaction"]["outputs"]
            for o in outputs:
                code_hash = o["lock"]["code_hash"]
                if code_hash == lock_type_hash:
                    cnt += 1
                    amount += convert_int(o["capacity"])
        return (cnt, amount)
    except:
        return (cnt, amount)


get_result = RpcGet(web3_url)
gw_rpc = GodwokenRpc(gw_rpc_url)
ckb_indexer = CKBIndexer(ckb_indexer_url)
ckb_rpc = CkbRpc(ckb_rpc_url)
gw_config = mainnet_config() if net_env.lower() == "mainnet" else testnet_config()
if net_env is None:
    print("net_env is None, use testnet config")
    gw_config = testnet_config()
else:
    net_env = net_env.lower()
    if net_env == "mainnet":
        gw_config = mainnet_config()
    elif net_env == "testnet":
        gw_config = testnet_config()
    else:
        print("use devnet")
        rollup_result_path = os.environ["ROLLUP_RESULT_PATH"]
        scripts_result_path = os.environ["SCRIPTS_RESULT_PATH"]
        gw_config = devnet_config(rollup_result_path, scripts_result_path)
        if gw_config == -1:
            print(
                "the env var: [ROLLUP_RESULT_PATH] and [SCRIPTS_RESULT_PATH] are not found, use testnet"
            )
            gw_config = testnet_config()

sched_custodian = SchedCustodian(ckb_indexer_url, gw_config)
print("wait on custodian for the first time...")
while sched_custodian.get_custodian() is None:
    sleep(1000)

@NodeFlask.route("/metrics/godwoken")
def exporter():
    registry = CollectorRegistry(auto_describe=False)

    last_block_number = Gauge(
        "Node_Get_LastBlockNumber", "LAST_BLOCK_NUMBER", ["web3_url"], registry=registry
    )

    node_gw_ping = Gauge(
        "Node_Get_Gw_Ping", "Node_GW_PING", ["web3_url", "gw_ping"], registry=registry
    )
    node_web3_clientVersion = Info(
        "Node_Get_Web3_ClientVersion",
        "Node_Web3_ClientVersion",
        ["web3_url"],
        registry=registry,
    )

    node_LastBlockInfo = Gauge(
        "Node_Get_LastBlockInfo",
        "Get LastBlockInfo, label include last_block_hash, last_blocknumber. value is last_block_timestamp;",
        ["web3_url", "last_block_hash", "last_blocknumber", "last_block_timestamp"],
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
            "total_amount": Gauge(
                "Node_" + v["name"] + "_TotalAmount",
                "Get sudt: " + v["name"] + " total amount",
                ["web3_url"],
                registry=registry,
            ),
            "finalized_amount": Gauge(
                "Node_" + v["name"] + "_FinalizedAmount",
                "Get sudt: " + v["name"] + " finalized amount",
                ["web3_url"],
                registry=registry,
            ),
            "count": Gauge(
                "Node_" + v["name"] + "_Count",
                "Get sudt: " + v["name"] + " count",
                ["web3_url"],
                registry=registry,
            ),
        }
        for k, v in token_dict.items()
    }
    print(sudt_guage_dict)

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

    LastBlockHeight = get_result.get_LastBlockHeight()
    if "-1" in LastBlockHeight.values():
        print(LastBlockHeight)
    else:
        last_block_number.labels(web3_url=web3_url).set(
            LastBlockHeight["last_blocknumber"]
        )

    gw_ping = get_result.get_gw_ping()
    if "-1" in gw_ping.values():
        print(gw_ping)
    else:
        node_gw_ping.labels(web3_url=web3_url, gw_ping=gw_ping["gw_ping_status"]).set(1)

    web3_clientVersion = get_result.web3_clientVersion()
    if "-1" in web3_clientVersion.values():
        print(web3_clientVersion)
    else:
        node_web3_clientVersion.labels(web3_url=web3_url).info(web3_clientVersion)

    LastBlockHash = get_result.get_LastBlockHash()
    LastBlockDetail = get_result.get_BlockDetail(LastBlockHash["last_block_hash"])
    if "-1" in LastBlockDetail.values():
        print(LastBlockDetail)
    else:
        PreviousBlock_hash = get_result.get_block_hash(
            hex((LastBlockDetail["blocknumber"]) - 1)
        )
        PreviousBlockDetail = get_result.get_BlockDetail(
            PreviousBlock_hash["blocknumber_hash"]
        )
        LastBlock_Time = convert_int(LastBlockDetail["blocknumber_timestamp"])
        PreviousBlock_Time = convert_int(PreviousBlockDetail["blocknumber_timestamp"])
        TimeDifference = abs(LastBlock_Time - PreviousBlock_Time)
        node_LastBlockInfo.labels(
            web3_url=web3_url,
            last_block_hash=LastBlockHash["last_block_hash"],
            last_blocknumber=LastBlockDetail["blocknumber"],
            last_block_timestamp=LastBlockDetail["blocknumber_timestamp"],
        ).set(TimeDifference)

        node_BlockDetail_transactions.labels(web3_url=web3_url).set(
            LastBlockDetail["commit_transactions"]
        )

        node_BlockTimeDifference.labels(web3_url=web3_url).set(TimeDifference)

    one_ckb = 100_000_000
    custodian_stats = get_custodian(
        ckb_indexer_url, gw_config, LastBlockDetail["blocknumber"]
    )
    if custodian_stats:
        sudt_stats = custodian_stats.sudt_stats
        capacity = custodian_stats.capacity
        finalized_capacity = custodian_stats.finalized_capacity
        cell_count = custodian_stats.cell_count
        ckb_cell_count = custodian_stats.ckb_cell_count
        capacity = int(capacity / one_ckb)
        gw_custodian_capacity.labels(web3_url).set(capacity)
        finalized_capacity = int(finalized_capacity / one_ckb)
        gw_custodian_finalized_capacity.labels(web3_url).set(finalized_capacity)
        gw_custodian_cell_count.labels(web3_url).set(cell_count)
        gw_custodian_ckb_cell_count.labels(web3_url).set(ckb_cell_count)

        for args, stats in sudt_stats.items():
            sudt_guage = sudt_guage_dict[args]
            total_amount_guage = sudt_guage["total_amount"]
            finalized_amount_guage = sudt_guage["finalized_amount"]
            count_guage = sudt_guage["count"]
            total_amount_guage.labels(web3_url).set(stats.total_amount)
            finalized_amount_guage.labels(web3_url).set(stats.finalized_amount)
            count_guage.labels(web3_url).set(stats.count)

    cnt, amount = get_gw_stat_by_lock(
        "deposit_lock", gw_rpc, LastBlockHash["last_block_hash"], ckb_rpc
    )
    gw_deposit_cnt.labels(web3_url=web3_url).set(cnt)
    amount = int(amount / one_ckb)
    gw_deposit_capacity.labels(web3_url=web3_url).set(amount)
    cnt, amount = get_gw_stat_by_lock(
        "withdrawal_lock", gw_rpc, LastBlockHash["last_block_hash"], ckb_rpc
    )
    amount = int(amount / one_ckb)
    gw_withdrawal_cnt.labels(web3_url=web3_url).set(cnt)
    gw_withdrawal_capacity.labels(web3_url=web3_url).set(amount)

    return Response(prometheus_client.generate_latest(registry), mimetype="text/plain")
