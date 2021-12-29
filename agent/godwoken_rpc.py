import requests
from agent.utils import convert_int


class GodwokenRpc:
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
        headers = {"Content-Type": "application/json"}
        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "gw_get_block_committed_info",
            "params": [block_hash],
        }
        try:
            r = requests.post(url="%s" % (self.url), json=payload, headers=headers)
            return r.json()
        except:
            return {"result": "-1"}

    def get_block_by_number(self, number):
        headers = {"Content-Type": "application/json"}
        data = (
            '{"id":2, "jsonrpc":"2.0", "method":"gw_get_block_by_number", "params":["%s"]}'
            % (number)
        )
        try:
            r = requests.post(url="%s" % (self.web3_url), data=data, headers=headers)
            replay = r.json()["result"]
            print(replay)
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
