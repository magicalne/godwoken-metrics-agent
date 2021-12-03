from agent.ckb_indexer import CKBIndexer
import  time

from multiprocessing.pool import ApplyResult, ThreadPool

class SchedCustodian:

	def __init__(self, ckb_indexer_url, gw_config):
		self.ckb_indexer_url = ckb_indexer_url
		self.gw_config = gw_config
		self.is_processing = False
		self.task: ApplyResult = None
		self.result = None

	def get_custodian(self):
		if self.is_processing:
			if self.task.ready():
				print("Ready.")
				self.is_processing = False
				return self.task.get()
			else:
				return None

		pool = ThreadPool(processes=1)
		self.task = pool.apply_async(get_custodian, (self.ckb_indexer_url, self.gw_config))
		self.is_processing = True
		return None


def get_custodian(ckb_index_url, gw_config):
	ckb_indexer = CKBIndexer(ckb_index_url)
	return ckb_indexer.get_custodian_ckb(gw_config)
	