import unittest
from agent.app import RpcGet


class RPCTest(unittest.TestCase):

    def setUp(self) -> None:
        self.rpc = RpcGet("localhost", 8024)

    def test_ping(self):
        res = self.rpc.get_gw_ping()
        print(res)

    def test_get_tip_block_hash(self):
        res = self.rpc.get_tip_block_hash()
        print(res)

    def test_get_block(self):
        res = self.rpc.get_tip_block_hash()
        res = self.rpc.get_block(res['tip_block_hash'])
        print(res)

    def test_get_peerCount(self):
        res = self.rpc.get_NetPeerCount()
        print(res)

    def test_get_version(self):
        res = self.rpc.get_net_version()
        print(res)

    def test_get_LasteBlockInfo(self):
        res = self.rpc.get_LastBlockInfo()
        print(res)

    def test_get_block_by_number(self):
        res = self.rpc.get_block_by_number(1)
        print(res)
