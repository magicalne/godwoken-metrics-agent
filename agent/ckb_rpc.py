import traceback
import requests


class CkbRpc:

    def __init__(self, url):
        self.url = url

    def get_transaction(self, tx):
        headers = {"Content-Type": "application/json"}
        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "get_transaction",
            "params": [
                tx
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

    def get_live_cell(self, index, tx_hash):
        headers = {"Content-Type": "application/json"}
        payload = {"id":1, "jsonrpc":"2.0", "method":"get_live_cell", "params":[{
            "tx_hash": tx_hash,
            "index": index
        },
        True
        ]}
        try:
            r = requests.post(
                url="%s" % (self.url),
                json=payload,
                headers=headers
            )
            
            return r.json()
        except Exception:
            print(traceback.format_exc())

            return {
                "result": "-1"
            }
