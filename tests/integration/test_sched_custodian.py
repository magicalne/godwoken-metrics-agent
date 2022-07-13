from time import sleep
import unittest
from agent.sched_custodian import get_custodian 
from agent.gw_config import testnet_config


class TestSchedCustodian(unittest.TestCase):
    def setUp(self) -> None:
        self.gw_config = testnet_config()
        self.indexer_url = "https://testnet.ckb.dev/indexer"

    def test_get_custodian(self) -> None:
        custodian = get_custodian(self.indexer_url, self.gw_config, 171987)
        print(f'custodian: {custodian}')
