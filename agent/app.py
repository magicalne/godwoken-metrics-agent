# encoding: utf-8

import requests
import prometheus_client
from prometheus_client.core import CollectorRegistry, Gauge, Info
from flask import Response, Flask
import sys


NodeFlask = Flask(__name__)
web3_url = sys.argv[1]


def convert_int(value):
    try:
        return int(value)
    except ValueError:
        return int(value, base=16)
    except Exception as exp:
        raise exp


class RpcGet(object):
    def __init__(self, web3_url):
        self.web3_url = web3_url

    def get_LastBlockHeight(self):
        headers = {"Content-Type": "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"eth_blockNumber", "params":[]}'
        try:
            r = requests.post(
                url="%s" % (self.web3_url),
                data=data,
                headers=headers
            )
            replay = r.json()["result"]
            return {
                "last_blocknumber": convert_int(replay)
            }
        except:
            return {
                "last_blocknumber": "-1"
            }

    def get_LastBlockHash(self):
        headers = {"Content-Type": "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"gw_get_tip_block_hash", "params":[]}'
        try:
            r = requests.post(
                url="%s" % (self.web3_url),
                data=data,
                headers=headers
            )
            replay = r.json()["result"]
            return {
                "last_block_hash": str(replay)
            }
        except:
            return {
                "last_block_hash": "-1"
            }

    def get_BlockDetail(self, block_hash):
        headers = {"Content-Type":  "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"gw_get_block", "params":["%s"]}' % (
            block_hash)
        try:
            r = requests.post(
                url="%s" % (self.web3_url),
                data=data,
                headers=headers
            )
            replay = r.json()["result"]
            return {
                "blocknumber": convert_int(replay["block"]["raw"]["number"]),
                "parent_block_hash": replay['block']['raw']['parent_block_hash'],
                "commit_transactions": len(replay["block"]["transactions"]),
                "transactions": replay["block"]["transactions"],
                "blocknumber_timestamp": convert_int(replay["block"]["raw"]["timestamp"])
            }
        except:
            return {
                "blocknumber": "-1",
                "parent_block_hash": "-1",
                "commit_transactions": "-1",
                "transactions": [],
                "blocknumber_timestamp": "-1"
            }

    def get_BlockDetailByNumber(self, number):
        headers = {"Content-Type":  "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"gw_get_block_by_number", "params":["%s"]}' % (
            number)
        try:
            r = requests.post(
                url="%s" % (self.web3_url),
                data=data,
                headers=headers
            )
            replay = r.json()["result"]
            return {
                "blocknumber": convert_int(replay["block"]["raw"]["number"]),
                "commit_transactions": len(replay["block"]["transactions"]),
                "transactions": replay["block"]["transactions"],
                "blocknumber_timestamp": convert_int(replay["block"]["raw"]["timestamp"])
            }
        except:
            return {
                "blocknumber": "-1",
                "commit_transactions": "-1",
                "transactions": [],
                "blocknumber_timestamp": "-1"
            }

    def get_block_hash(self, blocknumber):
        headers = {"Content-Type":  "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"gw_get_block_hash", "params":["%s"]}' % (
            blocknumber)
        try:
            r = requests.post(
                url="%s" % (self.web3_url),
                data=data,
                headers=headers
            )
            replay = r.json()["result"]
            return {
                "blocknumber_hash": str(replay)
            }
        except:
            return {
                "blocknumber_hash": "-1"
            }

    def get_gw_ping(self):
        headers = {"Content-Type": "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"gw_ping", "params":[]}'
        try:
            r = requests.post(
                url="%s" % (self.web3_url),
                data=data,
                headers=headers
            )
            replay = r.json()["result"]
            return {
                "gw_ping_status": replay
            }
        except:
            return {
                "gw_ping_status": "-1"
            }

    def web3_clientVersion(self):
        headers = {"Content-Type": "application/json"}
        data = '{"id":1, "jsonrpc":"2.0", "method":"web3_clientVersion", "params":[]}'
        try:
            r = requests.post(
                url="%s" % (self.web3_url),
                data=data,
                headers=headers
            )
            replay = r.json()["result"]
            return {
                "web3_clientVersion": replay
            }
        except:
            return {
                "web3_clientVersion": "-1"
            }

# flask object


get_result = RpcGet(web3_url)


@NodeFlask.route("/metrics/godwoken")
def exporter():
    registry = CollectorRegistry(auto_describe=False)

    last_block_number = Gauge("Node_Get_LastBlockNumber",
                              "LAST_BLOCK_NUMBER", ["web3_url"],
                              registry=registry)

    node_gw_ping = Gauge("Node_Get_Gw_Ping",
                         "Node_GW_PING", ["web3_url", "gw_ping"],
                         registry=registry)
    node_web3_clientVersion = Info("Node_Get_Web3_ClientVersion",
                                   "Node_Web3_ClientVersion", ["web3_url"],
                                   registry=registry)

    node_LastBlockInfo = Gauge("Node_Get_LastBlockInfo",
                               "Get LastBlockInfo, label include last_block_hash, last_blocknumber. value is last_block_timestamp;",
                               ["web3_url", "last_block_hash",
                                "last_blocknumber", "last_block_timestamp"],
                               registry=registry)

    node_BlockDetail_transactions = Gauge("Node_Get_BlockDetail_transactions",
                                          "Get LastTxInfo, label include last_block_hash, tx_hash. value is proposal_transactions in block;",
                                          ["web3_url"],
                                          registry=registry)

    node_BlockTimeDifference = Gauge("Node_Get_BlockTimeDifference",
                                     "Get current bloack time and previous block time,value is Calculate the difference into seconds;",
                                     ["web3_url"],
                                     registry=registry)

    LastBlockHeight = get_result.get_LastBlockHeight()
    if "-1" in LastBlockHeight.values():
        print(LastBlockHeight)
    else:
        last_block_number.labels(
            web3_url=web3_url
        ).set(LastBlockHeight["last_blocknumber"])

    gw_ping = get_result.get_gw_ping()
    if "-1" in gw_ping.values():
        print(gw_ping)
    else:
        node_gw_ping.labels(
            web3_url=web3_url,
            gw_ping=gw_ping["gw_ping_status"]
        ).set(1)

    web3_clientVersion = get_result.web3_clientVersion()
    if "-1" in web3_clientVersion.values():
        print(web3_clientVersion)
    else:
        node_web3_clientVersion.labels(
            web3_url=web3_url
        ).info(web3_clientVersion)

    LastBlockHash = get_result.get_LastBlockHash()
    LastBlockDetail = get_result.get_BlockDetail(
        LastBlockHash["last_block_hash"])
    if "-1" in LastBlockDetail.values():
        print(LastBlockDetail)
    else:
        PreviousBlock_hash = get_result.get_block_hash(
            hex((LastBlockDetail["blocknumber"]) - 1))
        PreviousBlockDetail = get_result.get_BlockDetail(
            PreviousBlock_hash["blocknumber_hash"])
        LastBlock_Time = convert_int(LastBlockDetail["blocknumber_timestamp"])
        PreviousBlock_Time = convert_int(
            PreviousBlockDetail["blocknumber_timestamp"])
        TimeDifference = abs(LastBlock_Time - PreviousBlock_Time)
        node_LastBlockInfo.labels(
            web3_url=web3_url,
            last_block_hash=LastBlockHash["last_block_hash"],
            last_blocknumber=LastBlockDetail["blocknumber"],
            last_block_timestamp=LastBlockDetail["blocknumber_timestamp"]
        ).set(TimeDifference)

        node_BlockDetail_transactions.labels(
            web3_url=web3_url
        ).set(LastBlockDetail["commit_transactions"])

        node_BlockTimeDifference.labels(
            web3_url=web3_url
        ).set(TimeDifference)

    return Response(prometheus_client.generate_latest(registry), mimetype="text/plain")
