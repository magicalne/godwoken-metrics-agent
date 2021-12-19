from time import sleep
import unittest
from agent.sched_cuustodian import SchedCustodian
from agent.gw_config import testnet_config


class TestSchedCustodian(unittest.TestCase):
    def setUp(self) -> None:
        gw_config = testnet_config()
        self.sched = SchedCustodian("https://testnet.ckb.dev/indexer", gw_config)

    def test(self):
        while True:
            res = self.sched.get_custodian(60000000000)
            if res is not None:
                print(res)
                return
            print("sleep 1 sec...")
            sleep(1)
