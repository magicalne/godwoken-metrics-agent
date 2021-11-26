import requests
import traceback


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

