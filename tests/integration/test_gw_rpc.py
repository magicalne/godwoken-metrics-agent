from pprint import pprint
import logging
import unittest

from agent.godwoken_rpc import GodwokenRpc


class TestGwRpc(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
        # url = "http://18.167.4.134:30119"
        url = "https://godwoken-testnet-web3-rpc.ckbapp.dev"
        self.client = GodwokenRpc(url)

    def test_gw_get_block_committed_info(self):
        res = self.client.gw_get_block_committed_info("0xd99f0f5cf146a4ceba4d4e12bd0fff598593c214d516e43e5b49119464550184")
        print(res)

    def test_get_tip_block_hash(self):
        print(self.client.get_tip_block_hash())

    def test_get_block(self):
        block_hash = '0x9155aa15998c047064d8472aeb80604748a273c5c9ae0a04eadd494689b51ec9'
        print(self.client.get_block(block_hash)['result']['block']['raw']['number'])

    def test_get_tip_number(self):
        tip_number = self.client.get_tip_number()
        print(f"tip number: {tip_number}")
        block = self.client.get_block_by_number(hex(tip_number))
        pprint(block, depth=3, indent=2)

    def test_ping(self):
        print(self.client.ping())
