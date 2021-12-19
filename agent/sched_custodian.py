import traceback
from agent.ckb_indexer import CKBIndexer
import time

from multiprocessing.pool import ApplyResult, ThreadPool


class SchedCustodian:
    def __init__(self, ckb_indexer_url, gw_config):
        self.ckb_indexer_url = ckb_indexer_url
        self.gw_config = gw_config
        self.is_processing = False
        self.task: ApplyResult = None
        self.result = None
        self.pool = ThreadPool(processes=1)

    def get_custodian(self, last_block_number):
        if self.is_processing:
            if self.task.ready():
                print("Ready.")
                self.is_processing = False
                try:
                    return self.task.get()
                except:
                    print("task failed: {}".format(traceback.print_exc()))
            else:
                print("Processing...")
                return None

        self.task = self.pool.apply_async(
            get_custodian(self.ckb_indexer_url, self.gw_config, last_block_number)
        )
        self.is_processing = True
        return None


def get_custodian(ckb_index_url, gw_config, last_block_number):
    try:
        ckb_indexer = CKBIndexer(ckb_index_url)
        last_finalized_block_numbrer = last_block_number - 450
        return ckb_indexer.get_custodian_stats(gw_config, last_finalized_block_numbrer)
    except:
        print("get custodian stats with error: {}".format(traceback.print_exc()))
