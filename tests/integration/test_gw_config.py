import unittest
from pprint import pformat
from agent.gw_config import testnet_config, mainnet_config, mainnet_v1_config, testnet_v1_1_config


class TestGwConfig(unittest.TestCase):

    def test(self):
        print('testnet v0')
        print(testnet_config().get_rollup_type_hash())
        print('mainnet v0')
        print(mainnet_config().get_rollup_type_hash())
        print('mainnet v1')
        print(mainnet_v1_config().get_rollup_type_hash())
        print('testnet v1')
        print(testnet_v1_1_config().get_rollup_type_hash())
