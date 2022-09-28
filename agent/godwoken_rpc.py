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

    def get_block_by_number(self, number):
        return self.submit(method="gw_get_block_by_number", params=[number])

    def get_tip_block_hash(self):
        return self.submit(method="gw_get_tip_block_hash", params=[])

    def get_block(self, block_hash):
        return self.submit(method="gw_get_block", params=[block_hash])

    def get_tip_number(self):
        tip_block_hash = self.get_tip_block_hash()
        tip = self.get_block(tip_block_hash)
        tip_number = tip['block']['raw']['number']
        return convert_int(tip_number)

    def ping(self):
        return self.submit(method="gw_ping", params=[])
