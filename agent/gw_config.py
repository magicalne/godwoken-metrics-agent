import json
import requests


class GwConfig:
	rollup_result: dict = {}
	scripts_result: dict = {}

	def __init__(self, rollup_result, scripts_result):
		self.rollup_result = rollup_result
		self.scripts_result = scripts_result

	def get_rollup_type_hash(self) -> str:
		return self.rollup_result['rollup_type_hash']
	
	def get_lock_type_hash(self, lock: str) -> str:
		for k in self.scripts_result:
			if k == lock:
				return self.scripts_result[k]['script_type_hash']
		return None


def get_config(prefix_url, scirpts_result_name, rollup_result_name):
	scripts_results_url = prefix_url % scirpts_result_name
	scripts_result = requests.get(scripts_results_url).json()
	rollup_result_url = prefix_url % rollup_result_name
	rollup_result = requests.get(rollup_result_url).json()
	return GwConfig(rollup_result=rollup_result, scripts_result=scripts_result)


def mainnet_config():
	url = "https://raw.githubusercontent.com/nervosnetwork/godwoken-public/master/mainnet/config/%s"
	return get_config(prefix_url=url, scirpts_result_name="scripts-result.json", rollup_result_name="rollup-result.json")

	
def testnet_config():
	url = "https://raw.githubusercontent.com/nervosnetwork/godwoken-public/master/testnet/config/%s"
	return get_config(prefix_url=url, scirpts_result_name="scripts-deploy-result.json", rollup_result_name="genesis.json")

def devnet_config(rollup_result_path, scripts_result_path):
	if rollup_result_path is not None and scripts_result_path is not None:
		with open(rollup_result_path) as f:
			rollup_result = json.load(f)

		with open(scripts_result_path) as f:
			scripts_result = json.load(f)
		return GwConfig(rollup_result, scripts_result)
	else:
		return -1
