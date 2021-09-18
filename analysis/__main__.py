from agent.app import convert_int, RpcGet
from agent.tx import TxStats
import sys
if __name__ == "__main__":
    ## "https://godwoken-testnet-web3-rpc.ckbapp.dev"
    web3_url = sys.argv[1]
    rpc = RpcGet(web3_url)
    stats = TxStats(rpc, 24*3600, 10)
    stats.sync_block()
    from_id, to_id = stats.stats()
    print(from_id)
    print(to_id)

