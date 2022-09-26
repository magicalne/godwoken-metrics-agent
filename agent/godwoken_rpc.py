from sys import meta_path
import requests
import logging
from agent.utils import convert_int
from agent.json_rpc import JsonRPC


class GodwokenRpc(JsonRPC):

    def __init__(self, url):
        self.url = url

    """
    response:
    L2BlockCommittedInfo {
        number
        block_hash
        transaction_hash
    }
    """

    def gw_get_block_committed_info(self, block_hash):
        return self.submit(method="gw_get_block_committed_info", params=[block_hash])
        #headers = {"Content-Type": "application/json"}
        #payload = {
        #    "id": 1,
        #    "jsonrpc": "2.0",
        #    "method": "gw_get_block_committed_info",
        #    "params": [block_hash],
        #}
        #try:
        #    r = requests.post(url="%s" % (self.url),
        #                      json=payload,
        #                      headers=headers)
        #    return r.json()
        #except:
        #    logging.exception("Error get block committed info. block hash %s",
        #                      block_hash)
        #    return {"result": "-1"}

    def get_block_by_number(self, number):
        return self.submit(method="gw_get_block_by_number", params=[number])
        
        ##headers = {"Content-Type": "application/json"}
        ##data = (
        ##    '{"id":2, "jsonrpc":"2.0", "method":"gw_get_block_by_number", "params":["%s"]}'
        ##    % (number))
        ##try:
        ##    r = requests.post(url="%s" % (self.web3_url),
        ##                      data=data,
        ##                      headers=headers)
        ##    replay = r.json()["result"]
        ##    print(replay)
        ##    return {
        ##        "blocknumber":
        ##        convert_int(replay["block"]["raw"]["number"]),
        ##        "commit_transactions":
        ##        len(replay["block"]["transactions"]),
        ##        "transactions":
        ##        replay["block"]["transactions"],
        ##        "blocknumber_timestamp":
        ##        convert_int(replay["block"]["raw"]["timestamp"]),
        ##    }
        ##except:
        ##    return {
        ##        "blocknumber": "-1",
        ##        "commit_transactions": "-1",
        ##        "transactions": [],
        ##        "blocknumber_timestamp": "-1",
        ##    }

    def get_tip_block_hash(self):
        return self.submit(method="gw_get_tip_block_hash", params=[])
        ##headers = {"Content-Type": "application/json"}
        ##payload = {
        ##    "id": 1,
        ##    "jsonrpc": "2.0",
        ##    "method": "gw_get_tip_block_hash",
        ##    "params": [],
        ##}
        ##try:
        ##    r = requests.post(url="%s" % (self.url),
        ##                      json=payload,
        ##                      headers=headers)
        ##    return r.json()
        ##except:
        ##    logging.exception("Error get tip block hash")
        ##    return {"result": "-1"}

    def get_block(self, block_hash):
        return self.submit(method="gw_get_block", params=[block_hash])
        #headers = {"Content-Type": "application/json"}
        #payload = {
        #    "id": 1,
        #    "jsonrpc": "2.0",
        #    "method": "gw_get_block",
        #    "params": [block_hash]
        #}
        #try:
        #    r = requests.post(url="%s" % (self.url),
        #                      json=payload,
        #                      headers=headers)
        #    return r.json()
        #except:
        #    logging.exception("Error get block")
        #    return {"result": "-1"}

    def get_tip_number(self):
        tip_block_hash = self.get_tip_block_hash()
        tip = self.get_block(tip_block_hash)
        tip_number = tip['block']['raw']['number']
        return convert_int(tip_number)

    def ping(self):
        return self.submit(method="gw_ping", params=[])
