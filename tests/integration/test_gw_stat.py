import unittest
from agent.ckb_rpc import CkbRpc
from agent.godwoken_rpc import GodwokenRpc
from agent.gw_config import testnet_config
from agent.gw_stat import GwStat


class TestGwStat(unittest.TestCase):
    def setUp(self):
        ckb_rpc = CkbRpc("https://testnet.ckb.dev/rp")
        config = testnet_config()
        gw_rpc = GodwokenRpc("http://18.167.4.134:30119")
        self.gw_rpc = gw_rpc
        self.test = GwStat(config, gw_rpc, ckb_rpc)

    def test_withdrawal(self):
        block = self.gw_rpc.get_block_by_number(221371)
        
        self.test.gw_stat_by_lock("withdrawal_lock", "")
