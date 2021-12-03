import requests
import traceback

from agent.utils import convert_int
from agent.gw_config import GwConfig


class CKBIndexer(object):

    def __init__(self, url):
        self.url = url


    def get_cells(self, code_hash, args, limit, cursor):
        limit = hex(limit)
        headers = {"Content-Type": "application/json"}
        payload = {"id":1, "jsonrpc":"2.0", "method":"get_cells", "params":[{
            "script": {
                "code_hash": code_hash,
                "hash_type": "type",
                "args": args
            },
            "script_type": "lock"
        },
        "desc",
        limit
        ]}
        if cursor is not None:
            payload['params'].append(cursor)
        try:
            r = requests.post(
                url="%s" % (self.url),
                json=payload,
                headers=headers
            )
            
            return r.json()
        except Exception:
            print(traceback.format_exc())

            return {
                "result": "-1"
            }

    def get_custodian_ckb(self, gw_config: GwConfig) -> int:
        custodian_script_type_hash = gw_config.get_lock_type_hash("custodian_lock")
        rollup_type_hash = gw_config.get_rollup_type_hash()
        capacity = 0
        cursor = None
        while True:
            limit = 1000
            res = self.get_cells(custodian_script_type_hash, rollup_type_hash, limit, cursor)
            if res['result'] == -1:
                return -1
            result = res['result']
            for cell in result['objects']:
                c = convert_int(cell['output']['capacity'])
                capacity += c

            cursor = result['last_cursor']
            if cursor == "0x":
                break
        return capacity