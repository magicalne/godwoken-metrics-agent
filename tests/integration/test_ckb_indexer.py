import unittest
from agent.ckb_indexer import CKBIndexer
class TestCkbIndexer(unittest.TestCase):

	def setUp(self) -> None:
		url = "https://testnet.ckb.dev/indexer"
		# url = "http://localhost:8116"
		self.client = CKBIndexer(url)

	def test_get_cell(self):
		res = self.client.get_cells("0x50fde68430caf9b2cb856cdecf9f35ea46f369ec02aa88d3237ca88620193fa0", "0x4cc2e6526204ae6a2e8fcf12f7ad472f41a1606d5b9624beebd215d780809f6a", 100, None)
		print(res)
