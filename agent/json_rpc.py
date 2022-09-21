import logging
from typing import List
import requests

from agent.error import RPCException


class JsonRPC:

    def __init__(self, url) -> None:
        self.url = url

    def submit(self, method: str, params: List):
        headers = {"Content-Type": "application/json"}
        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        try:
            r = requests.post(url="%s" % (self.url), json=payload, headers=headers)
            logging.info(f"Access {self.url} {method} status: {r.status_code}")
            r.raise_for_status()
            return r.json()["result"]
        except Exception as e:
            logging.error(f"Submit request to {self.url}, method: {method}, params: {params}", exc_info = e)
            raise RPCException from None
            

