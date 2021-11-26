import unittest
from agent.gw_config import testnet_config, mainnet_config

class TestGwConfig(unittest.TestCase):

	def test(self):

		print(testnet_config())
		print(mainnet_config())