import unittest
import pandas as pd
import json
from datetime import datetime, timedelta
from agent.ckb_indexer import CKBIndexer
from agent.gw_config import mainnet_config, testnet_config
from agent.tx import TxStats


class TestApp(unittest.TestCase):

    def setUp(self) -> None:
        self.rpc = RpcGet("https://godwoken-testnet-web3-rpc.ckbapp.dev")

    def test_ping(self):
        res = self.rpc.get_gw_ping()
        print(res)

    def test(self):
        last_block_hash = self.rpc.get_LastBlockHash()
        last_block = self.rpc.get_BlockDetail(
            last_block_hash["last_block_hash"])
        arr = [last_block]
        last_block_ts = datetime.fromtimestamp(
            int(last_block['blocknumber_timestamp'])/1000)
        print(last_block['commit_transactions'], last_block_ts)
        while True:
            block = self.rpc.get_BlockDetail(arr[-1]['parent_block_hash'])
            block_ts = datetime.fromtimestamp(
                int(block['blocknumber_timestamp'])/1000)
            print(block['commit_transactions'], block_ts)
            if last_block_ts - block_ts > timedelta(minutes=10):
                break
            arr.append(block)
        txs = []
        for block in arr:
            txs = txs + block['transactions']
        print(json.dumps(txs))
        df = pd.DataFrame(txs)
        print(df.describe())

    def test_sync(self):
        tx_stats = TxStats(self.rpc, 10*60, 10)
        tx_stats.sync_block()
        from_stats, to_stats = tx_stats.stats()
        print(from_stats.head())
        print(to_stats.head())

    # def test_get_custodian_ckb(self):
    #     config = mainnet_config()
    #     ckb_indexer = CKBIndexer("https://mainnet.ckbapp.dev/indexer")
    #     capacity = get_custodian_ckb(ckb_indexer, config)
    #     print(capacity)