import unittest

from agent.godwoken_rpc import GodwokenRpc

class TestGwRpc(unittest.TestCase):

	def setUp(self):
		url = "http://18.167.4.134:30119"
		self.client = GodwokenRpc(url)
	
	def test_gw_get_block_committed_info(self):
		res = self.client.gw_get_block_committed_info("0xd99f0f5cf146a4ceba4d4e12bd0fff598593c214d516e43e5b49119464550184")
		print(res)