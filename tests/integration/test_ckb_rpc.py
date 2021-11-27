import unittest
from agent.ckb_rpc import CkbRpc

class TestCkbRpc(unittest.TestCase):

	def setUp(self):
		testnet = "https://testnet.ckb.dev/rpc" 
		# mainnet = "https://mainnet.ckb.dev/rpc" 
		self.client = CkbRpc(testnet)

	def test_get_tx(self):
		res = self.client.get_transaction("0x8f372e7eafd53a257b2e131335ecc1eba8dc77d1ec62f60c7c572482a7326e0b")
		inputs = res['result']['transaction']['inputs']
		for i in inputs:
			print(i)
		outputs = res['result']['transaction']['outputs']
		for o in outputs:
			print(o)

	def test_get_live_cell(self):
		print(self.client.get_live_cell("0x33", "0x08fafaede8e1ed2a1cef87a9c69e71c7531e00d89add4ffd2064a9cabce66a94"))
