import requests


class GodwokenRpc(object):

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
            "params": [
                block_hash
            ]
        }
        try:
            r = requests.post(
                url="%s" % (self.url),
                json=payload,
                headers=headers
            )
            return r.json()
        except:
            return {
                "result": "-1"
            }

