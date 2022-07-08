import unittest
from pprint import pformat
from agent.gw_config import testnet_config, mainnet_config, mainnet_v1_config, testnet_v1_1_config


class TestGwConfig(unittest.TestCase):

    def test(self):
        print('testnet v0')
        testnet_v0 = testnet_config()
        print("rollup tyype hash: {0}, finality_blocks: {1}".format(testnet_v0.get_rollup_type_hash(), testnet_v0.finality_blocks))
        print('mainnet v0')
        mainnet_v0 = mainnet_config()
        print("rollup tyype hash: {0}, finality_blocks: {1}".format(mainnet_v0.get_rollup_type_hash(), mainnet_v0.finality_blocks))
        print('mainnet v1')
        mainnet_v1 = mainnet_v1_config()
        print("rollup tyype hash: {0}, finality_blocks: {1}".format(mainnet_v1.get_rollup_type_hash(), mainnet_v1.finality_blocks))
        print('testnet v1')
        testnet_v1 = testnet_v1_1_config()
        print("rollup tyype hash: {0}, finality_blocks: {1}".format(testnet_v1.get_rollup_type_hash(), testnet_v1.finality_blocks))
