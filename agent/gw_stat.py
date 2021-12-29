from agent.gw_config import GwConfig
from agent.ckb_rpc import CkbRpc
from agent.godwoken_rpc import GodwokenRpc
from agent.utils import convert_int


class GwStat:
    def __init__(self, config: GwConfig, gw_rpc: GodwokenRpc, ckb_rpc: CkbRpc) -> None:
        self.config = config
        self.gw_rpc = gw_rpc
        self.ckb_rpc = ckb_rpc

    def gw_stat_by_lock(self, lock_name: str, block_hash: str):
        lock_type_hash = self.config.get_lock_type_hash(lock_name)
        res = self.gw_rpc.gw_get_block_committed_info(block_hash)
        tx = res["result"]["transaction_hash"]
        res = self.ckb_rpc.get_transaction(tx)
        inputs = res["result"]["transaction"]["inputs"]
        cnt = 0
        amount = 0
        if inputs is None or len(inputs) == 0:
            return (cnt, amount)
        try:
            for i in inputs:
                tx_hash = i["previous_output"]["tx_hash"]
                res = self.ckb_rpc.get_transaction(tx_hash)
                outputs = res["result"]["transaction"]["outputs"]
                for o in outputs:
                    code_hash = o["lock"]["code_hash"]
                    if code_hash == lock_type_hash:
                        cnt += 1
                        amount += convert_int(o["capacity"])
            return (cnt, amount)
        except:
            return (cnt, amount)
