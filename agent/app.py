# encoding: utf-8

import requests
import prometheus_client
from prometheus_client import Gauge
from prometheus_client.core import CollectorRegistry
from flask import Response, Flask, request, current_app
import os
import sys

NodeFlask = Flask(__name__)


def convert_int(value):
    try:
        return int(value)
    except ValueError:
        return int(value, base=16)
    except Exception as exp:
        raise exp


class RpcGet(object):
    def __init__(self, NodeIP, NodePort):
        self.NodeIP = NodeIP
        self.NodePort = NodePort

    def get_gw_ping(self):
        headers = {"Content-Type":  "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"gw_ping", "params":[]}'
        try:
            r = requests.post(
                url="http://%s:%s" % (self.NodeIP, self.NodePort),
                data=data,
                headers=headers
            )
            replay = r.json()["result"]
            return {
                "result": replay
            }
        except:
            return {
                "result": "-1"
            }

    def get_tip_block_hash(self):
        headers = {"Content-Type":  "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"gw_get_tip_block_hash", "params":[]}'
        try:
            r = requests.post(
                url="http://%s:%s" % (self.NodeIP, self.NodePort),
                data=data,
                headers=headers
            )
            replay = r.json()["result"]
            return {
                "tip_block_hash": replay
            }
        except:
            return {
                "tip_block_hash": "-1"
            }

    def get_block(self, hash):
        headers = {"Content-Type":  "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"gw_get_block", "params":["%s"]}' % (
            hash)
        try:
            r = requests.post(
                url="http://%s:%s" % (self.NodeIP, self.NodePort),
                data=data,
                headers=headers
            )
            return r.json()["result"]
        except:
            return {
                "status": "error"
            }

    def get_NetPeerCount(self):
        headers = {"Content-Type":  "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"net_peerCount", "params":[]}'
        try:
            r = requests.post(
                url="http://%s:%s" % (self.NodeIP, self.NodePort),
                data=data,
                headers=headers
            )
            replay = r.json()['result']
            peer_count = int(replay, 0)
            return {
                "peer_count": peer_count
            }
        except:
            return {
                "peer_count": -1
            }

    def get_net_version(self):
        headers = {"Content-Type":  "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"net_version", "params":[]}'
        try:
            r = requests.post(
                url="http://%s:%s" % (self.NodeIP, self.NodePort),
                data=data,
                headers=headers
            )
            replay = r.json()["result"]

            return {
                "version": int(replay, 0)
            }
        except:
            return {
                "version": "-1"
            }

    def get_LastBlockInfo(self):
        try:
            hash = self.get_tip_block_hash()['tip_block_hash']
            block_info = self.get_block(hash)['block']['raw']
            return {
                "last_blocknumber": int(block_info['number'], 0),
                "last_block_hash": hash,
                "last_block_timestamp": int(block_info["timestamp"], 0)
            }
        except:
            return {
                "last_blocknumber": "-1",
                "last_block_hash": "-1",
                "last_block_timestamp": "-1"
            }

    def get_block_hash(self):
        headers = {"Content-Type":  "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"gw_get_block_hash", "params":[]}'
        try:
            r = requests.post(
                url="http://%s:%s" % (self.NodeIP, self.NodePort),
                data=data,
                headers=headers
            )
            replay = r.json()["result"]
            return {
                "block_hash": replay
            }
        except:
            return {
                "block_hash": "-1"
            }

    def get_block_by_number(self, block_number):
        headers = {"Content-Type":  "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"gw_get_block_by_number", "params":["%s"]}' % (
            hex(block_number))
        try:
            r = requests.post(
                url="http://%s:%s" % (self.NodeIP, self.NodePort),
                data=data,
                headers=headers
            )
            return r.json()['result']
        except:
            return {
                "status": "error"
            }
        ################################################################################

    def _get_LastBlockInfo(self):
        headers = {"Content-Type": "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"get_tip_header", "params":[]}'
        try:
            r = requests.post(
                url="http://%s:%s" % (self.NodeIP, self.NodePort),
                data=data,
                headers=headers
            )
            replay = r.json()["result"]
            return {
                "last_blocknumber": convert_int(replay["number"]),
                "last_block_hash": str(replay["hash"]),
                "last_block_timestamp": convert_int(replay["timestamp"])
            }
        except:
            return {
                "last_blocknumber": "-1",
                "last_block_hash": "-1",
                "last_block_timestamp": "-1"
            }

    def get_BlockDetail(self, block_hash):
        headers = {"Content-Type":  "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"get_block", "params":["%s"]}' % (
            block_hash)
        try:
            r = requests.post(
                url="http://%s:%s" % (self.NodeIP, self.NodePort),
                data=data,
                headers=headers
            )
            replay = r.json()["result"]
            return {
                "commit_transactions": len(replay["transactions"]),
                "blocknumber_timestamp": convert_int(replay["header"]["timestamp"]),
                "proposal_transactions": len(replay["proposals"]),
                "uncles": len(replay["uncles"])
            }
        except:
            return {
                "commit_transactions": "-1",
                "blocknumber_timestamp": "-1",
                "proposal_transactions": "-1",
                "uncles": "-1"
            }

    def get_node_info(self):
        headers = {"Content-Type":  "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"local_node_info", "params":[]}'
        try:
            r = requests.post(
                url="http://%s:%s" % (self.NodeIP, self.NodePort),
                data=data,
                headers=headers
            )
            replay = r.json()["result"]
            return {
                "node_addressse": str(replay["addresses"][0]["address"]),
                "node_id": replay["node_id"],
                "node_version": replay["version"],
                "node_status": 1
            }
        except:
            return {
                "node_addressse": "-1",
                "node_id": "-1",
                "node_version": "-1",
                "node_status": 0
            }

    def _get_block_hash(self, blocknumber, is_old_version):
        headers = {"Content-Type":  "application/json"}
        blocknumber = "{}".format(
            blocknumber) if is_old_version else "0x{:x}".format(blocknumber)
        data = '{"id":2, "jsonrpc":"2.0", "method":"get_block_hash", "params":["%s"]}' % (
            blocknumber)
        try:
            r = requests.post(
                url="http://%s:%s" % (self.NodeIP, self.NodePort),
                data=data,
                headers=headers
            )
            replay = r.json()["result"]
            return {
                "blocknumber_hash": replay
            }
        except:
            return {
                "blocknumber_hash": "-1"
            }

    def get_peer_count(self):
        headers = {"Content-Type":  "application/json"}
        data = '{"id":2, "jsonrpc":"2.0", "method":"get_peers", "params":[]}'
        try:
            r = requests.post(
                url="http://%s:%s" % (self.NodeIP, self.NodePort),
                data=data,
                headers=headers
            )
            replay = r.json()["result"]
            peer_outbound = len(
                [peer for peer in replay if peer['is_outbound']])
            return {
                'peer_inbound': len(replay) - peer_outbound,
                'peer_outbound': peer_outbound,
            }
        except:
            return {
                'peer_inbound': '-1',
                'peer_outbound': '-1',
            }

#


@ NodeFlask.route("/metrics/<int:NodePort>")
def Node_Get(NodePort):
    PublicIP = request.headers.get('Host').split(':')[0]
    NodeIP = current_app.config.get(
        'NodeIP', os.getenv('MONITOR_NODE_IP', '127.0.0.1'))
    host_location = os.getenv('HOST_CITY', 'unknown')
    gw_node_name = os.getenv('GW_NODE_NAME', 'unknown')

    GW_Chain = CollectorRegistry(auto_describe=False)
    Node_Status = Gauge("Node_Status",
                        "Get the running state of the script, return 1 when running; return 0 if it is not running;",
                        ["node_location", "GW_NODE_NAME"],
                        registry=GW_Chain)
    Node_Get_LocalInfo = Gauge("Node_Get_LocalInfo",
                               "Get node info, label include address, node_id, version. value is node status;",
                               ["version", "GW_NODE_NAME"],
                               registry=GW_Chain)
    Node_PeerCount = Gauge("Node_get_PeerCount",
                           "Get node connected peer count",
                           ["GW_NODE_NAME"],
                           registry=GW_Chain
                           )
    # Node_Get_PeerOutbound = Gauge(
    #     "Node_Get_PeerOutbound",
    #     "Get node connected peer outbound count",
    #     ["NodeIP", "NodePort", "node_location"],
    #     registry=GW_Chain,
    # )
    # Node_Get_PeerInbound = Gauge(
    #     "Node_Get_PeerInbound",
    #     "Get node connected peer inbound count",
    #     ["NodeIP", "NodePort", "node_location"],
    #     registry=GW_Chain,
    # )
    Node_Get_LastBlockInfo = Gauge("Node_Get_LastBlockInfo",
                                   "Get LastBlockInfo, label include last_block_hash, last_blocknumber. value is last_block_timestamp;",
                                   ["GW_NODE_NAME", "last_block_hash", "last_blocknumber",
                                    "node_location", "last_block_timestamp"],
                                   registry=GW_Chain)
    Node_Get_LastBlocknumber = Gauge("Node_Get_LastBlocknumber",
                                     "Get LastBlocknumber, value is last_blocknumber;",
                                     ["GW_NODE_NAME", "node_location"],
                                     registry=GW_Chain)
    Node_Get_BlockDetail = Gauge("Node_Get_BlockDetail",
                                 "Get LastTxInfo, label include last_block_hash, tx_hash. value is commit_transactions in block;",
                                 ["GW_NODE_NAME", "node_location"],
                                 registry=GW_Chain)
    # Node_Get_BlockDetail_proposal_transactions = Gauge("Node_Get_BlockDetail_proposal_transactions",
    #                                                    "Get LastTxInfo, label include last_block_hash, tx_hash. value is proposal_transactions in block;",
    #                                                    ["NodeIP", "NodePort",
    #                                                     "node_location"],
    #                                                    registry=GW_Chain)
    # Node_Get_BlockDetail_uncles = Gauge("Node_Get_BlockDetail_uncles",
    #                                     "Get LastTxInfo, label include last_block_hash, tx_hash. value is uncles in block;",
    #                                     ["NodeIP", "NodePort", "node_location"],
    #                                     registry=GW_Chain)
    Node_Get_BlockDifference = Gauge("Node_Get_BlockDifference",
                                     "Get current bloack time and previous block time,label include CurrentHeight, PreviousHeight. value is Calculate the difference into seconds;",
                                     ["CurrentHeight", "PreviousHeight",
                                         "node_location", "GW_NODE_NAME"],
                                     registry=GW_Chain)
    Node_Get_BlockTimeDifference = Gauge("Node_Get_BlockTimeDifference",
                                         "Get current bloack time and previous block time,value is Calculate the difference into seconds;",
                                         ["node_location", "GW_NODE_NAME"],
                                         registry=GW_Chain)
    #
    get_result = RpcGet(NodeIP, NodePort)
    # LocalInfo = get_result.get_node_info()

    # status = LocalInfo["node_status"]
    # is_old_version = LocalInfo['node_version'].startswith('0.20')
    PeerCount = get_result.get_NetPeerCount()['peer_count']
    ping_result = get_result.get_gw_ping()
    status = 1 if ping_result['result'] == 'pong' else -1
    version = get_result.get_net_version()['version']
    if status == 1:
        Node_Status.labels(
            node_location=host_location,
            GW_NODE_NAME=gw_node_name).set(status)
        #
        Node_Get_LocalInfo.labels(
            version=version,
            GW_NODE_NAME=gw_node_name
        ).set(status)

        Node_PeerCount.labels(GW_NODE_NAME=gw_node_name).set(PeerCount)
        # Node_Get_PeerOutbound.labels(
        #     NodeIP=PublicIP, NodePort=NodePort,
        #     node_location=host_location
        # ).set(PeerCount['peer_outbound'])
        # Node_Get_PeerInbound.labels(
        #     NodeIP=PublicIP, NodePort=NodePort,
        #     node_location=host_location
        # ).set(PeerCount['peer_inbound'])
        #
        LastBlockInfo = get_result.get_LastBlockInfo()
        if "-1" in LastBlockInfo.values():
            print(LastBlockInfo)
        else:
            last_block_timestamp = LastBlockInfo["last_block_timestamp"]
            Node_Get_LastBlockInfo.labels(
                last_block_hash=LastBlockInfo["last_block_hash"],
                last_blocknumber=LastBlockInfo["last_blocknumber"],
                last_block_timestamp=LastBlockInfo["last_block_timestamp"],
                node_location=host_location,
                GW_NODE_NAME=gw_node_name,
            ).set(last_block_timestamp)
            #
            Node_Get_LastBlocknumber.labels(
                GW_NODE_NAME=gw_node_name,
                node_location=host_location
            ).set(LastBlockInfo["last_blocknumber"])
            #
            # Previous_block_hash = get_result.get_block_hash(convert_int(
            #     LastBlockInfo["last_blocknumber"]) - 1, is_old_version)
            PreviousBloackDetail = get_result.get_block_by_number(
                LastBlockInfo["last_blocknumber"] - 1)
            previous_block_timestamp = int(
                PreviousBloackDetail['raw']['timestamp'], 0)
            # PreviousBloackTimestamp = PreviousBloackDetail["blocknumber_timestamp"]
            # print("最新区块的时间戳： ", int(LastBlockInfo["last_blocknumber"]), LastBlockInfo["last_block_hash"], int(LastBlockInfo["last_block_timestamp"]))
            # print("上一个区块的时间戳： ", int(LastBlockInfo["last_blocknumber"]) - 1", Previous_block_hash["blocknumber_hash"], int(PreviousBloackDetail["blocknumber_timestamp"]))
            # print(int(LastBlockInfo["last_block_timestamp"]) - int(PreviousBloackDetail["blocknumber_timestamp"]))
            TimeDifference = last_block_timestamp - previous_block_timestamp
            Node_Get_BlockDifference.labels(
                CurrentHeight=LastBlockInfo["last_blocknumber"],
                PreviousHeight=(LastBlockInfo["last_blocknumber"] - 1),
                node_location=host_location,
                GW_NODE_NAME=gw_node_name
            ).set(TimeDifference)
            Node_Get_BlockTimeDifference.labels(
                node_location=host_location,
                GW_NODE_NAME=gw_node_name
            ).set(TimeDifference)
        #
        # BlockDetail = get_result.get_BlockDetail(
        #     LastBlockInfo["last_block_hash"])
        # if "-1" in BlockDetail.values():
        #     print(BlockDetail)
        # else:
        #     Node_Get_BlockDetail.labels(
        #         NodeIP=PublicIP, NodePort=NodePort,
        #         node_location=host_location
        #     ).set(BlockDetail["commit_transactions"])
        #     #
        #     Node_Get_BlockDetail_proposal_transactions.labels(
        #         NodeIP=PublicIP, NodePort=NodePort,
        #         node_location=host_location
        #     ).set(BlockDetail["proposal_transactions"])
        #     #
        #     Node_Get_BlockDetail_uncles.labels(
        #         NodeIP=PublicIP, NodePort=NodePort,
        #         node_location=host_location
        #     ).set(BlockDetail["uncles"])
    elif status == 0:
        Node_Status.labels(
            node_location=host_location,
            GW_NODE_NAME=gw_node_name
        ).set(status)
        Node_Get_LocalInfo.labels(
            node_addressse="none",
            node_id="none",
            node_version="none",
            node_location=host_location,
            GW_NODE_NAME=gw_node_name
        ).set(status)
    return Response(prometheus_client.generate_latest(GW_Chain), mimetype="text/plain")
