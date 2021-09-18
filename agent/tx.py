from dataclasses import dataclass
import pandas as pd
from typing import OrderedDict
from agent.app import RpcGet, convert_int


class TxStats:

    def __init__(self, rpc: RpcGet, duration: int, top: int) -> None:
        self.rpc = rpc
        self.duration = duration
        self.cache = TxCache(duration, top)
        self.last_block_hash = None
        self.current_ts = None


    def sync_block(self):
        res = self.rpc.get_LastBlockHash()
        last_block_hash = res['last_block_hash']
        while True:
            block = self.rpc.get_BlockDetail(last_block_hash)
            ts = int(block['blocknumber_timestamp'])/1000
            txs = [Tx(tx['raw']['from_id'], tx['raw']['to_id'])
                   for tx in block['transactions']]
            self.cache.add(ts, txs)
            if self.current_ts is None:
                self.current_ts = ts
            if self.current_ts - ts > self.duration:
                break
            print("Syncing %s, still %d seconds left" % (last_block_hash, self.duration - self.current_ts + ts))
            last_block_hash = block['parent_block_hash']
        print("Sync finished.")

    def stats(self):
        return self.cache.stats()


class TxCache:

    # duration: in second
    # top: top N
    def __init__(self, duration: int, top: int) -> None:
        self.duration = duration
        self.top = top
        self.cache = OrderedDict()

    # ts: epoch timestamp in second
    # tsx: list of Tx
    def add(self, ts, txs):
        self.cache[ts] = txs
        # remove outdated items
        while True:
            top = next(iter(self.cache.keys()))
            if ts - top > self.duration:
                self.cache.popitem(last=False)
            else:
                break

    def stats(self):
        if len(self.cache) == 0:
            return 'still empty'
        txs = []
        for v in self.cache.values():
            txs = txs + v
        df = pd.DataFrame(txs)
        top = min(len(df), self.top)
        top_from = df['from_id'].value_counts().head(top)
        top_to = df['to_id'].value_counts().head(top)
        return (top_from, top_to)


@dataclass
class Tx:
    from_id: int
    to_id: int

    def __init__(self, from_id, to_id) -> None:
        self.from_id = convert_int(from_id)
        self.to_id = convert_int(to_id)
