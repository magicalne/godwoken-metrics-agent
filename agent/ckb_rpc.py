from agent.json_rpc import JsonRPC


class CkbRpc(JsonRPC):
    def __init__(self, url):
        self.url = url

    def get_transaction(self, tx):
        return self.submit(method="get_transaction", params=[tx])

    def get_live_cell(self, index, tx_hash):
        req = {
                "tx_hash": tx_hash,
                "index": index
        }
        return self.submit(method="get_live_cell", params=[req, True])
