import unittest
from agent.ckb_rpc import CkbRpc

class TestCkbRpc(unittest.TestCase):

	def setUp(self):
		# testnet = "https://testnet.ckb.dev/rpc" 
		mainnet = "https://mainnet.ckb.dev/rpc" 
		self.client = CkbRpc(mainnet)

	def test_get_tx(self):
		res = self.client.get_transaction("0x10bb232b79d455996a0860d7f800023c4176a7f2fa1253a755e9b1883b66a19b")
		inputs = res['result']['transaction']['inputs']
		for i in inputs:
			print(i)
		outputs = res['result']['transaction']['outputs']
		for o in outputs:
			print(o)

	def test_get_live_cell(self):
		print(self.client.get_live_cell("0x33", "0x08fafaede8e1ed2a1cef87a9c69e71c7531e00d89add4ffd2064a9cabce66a94"))
