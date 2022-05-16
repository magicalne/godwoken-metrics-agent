import unittest
from agent.ckb_rpc import CkbRpc
from agent.godwoken_rpc import GodwokenRpc
from agent.gw_config import testnet_config, testnet_v1_1_config
from agent.gw_stat import GwStat
from agent.app import get_gw_stat_by_lock


class TestGwStat(unittest.TestCase):

    def setUp(self):
        ckb_rpc = CkbRpc("https://testnet.ckb.dev/rpc")
        config = testnet_v1_1_config()
        # config = testnet_config()
        # gw_rpc = GodwokenRpc("http://18.167.4.134:30119")
        gw_rpc = GodwokenRpc("https://godwoken-betanet-v1.ckbapp.dev/")
        self.gw_rpc = gw_rpc
        self.test = GwStat(config, gw_rpc, ckb_rpc)

    def test_deposit(self):
        block_hash = self.gw_rpc.get_tip_block_hash()['result']
        print("tip: %s" % block_hash)
        stat = get_gw_stat_by_lock("deposit_lock", self.gw_rpc, block_hash,
                                   self.ckb_rpc, self.config)
        print(stat)

    def test_withdrawal(self):
        block = self.gw_rpc.get_block_by_number(11)

        self.test.gw_stat_by_lock("withdrawal_lock", "")
