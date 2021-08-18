# Godwoken metrics agent -- A simple http service for metrics collection.

This service collects metrics from [godwoken-web3](https://github.com/nervosnetwork/godwoken-web3).

## Build

Make sure install [pipenv](https://pipenv.pypa.io/en/latest/install/) first.

```shell
pipenv install
```

## Run

### Env

```shell
export MONITOR_NODE_IP=127.0.0.1 ## Optional
export GW_NODE_NAME=GW_NODE_ALPHA
```
### Spawn a service

```shell
pipenv run python -m agent 3004
```

`3004` is the port we are running on.

### Checkout some metrics

Suppose we have a web3 on `localhost:8024`. Then we can fire a request like below:

```shell
curl http://localhost:3004/metrics/8024
```

You should see something like below:

```
# HELP Node_Status Get the running state of the script, return 1 when running; return 0 if it is not running;
# TYPE Node_Status gauge
Node_Status{GW_NODE_NAME="GW_NODE_ALPHA",node_location="unknown"} 1.0
# HELP Node_Get_LocalInfo Get node info, label include address, node_id, version. value is node status;
# TYPE Node_Get_LocalInfo gauge
Node_Get_LocalInfo{GW_NODE_NAME="GW_NODE_ALPHA",version="1024777"} 1.0
# HELP Node_get_PeerCount Get node connected peer count
# TYPE Node_get_PeerCount gauge
Node_get_PeerCount{GW_NODE_NAME="GW_NODE_ALPHA"} 0.0
# HELP Node_Get_LastBlockInfo Get LastBlockInfo, label include last_block_hash, last_blocknumber. value is last_block_timestamp;
# TYPE Node_Get_LastBlockInfo gauge
Node_Get_LastBlockInfo{GW_NODE_NAME="GW_NODE_ALPHA",last_block_hash="0x4afc4de1c32d07f123f4275ecd37a308b736330f2bc3e3fd5024a5728a32f76b",last_block_timestamp="1629276017469",last_blocknumber="3892",node_location="unknown"} 1.629276017469e+012
# HELP Node_Get_LastBlocknumber Get LastBlocknumber, value is last_blocknumber;
# TYPE Node_Get_LastBlocknumber gauge
Node_Get_LastBlocknumber{GW_NODE_NAME="GW_NODE_ALPHA",node_location="unknown"} 3892.0
# HELP Node_Get_BlockDetail Get LastTxInfo, label include last_block_hash, tx_hash. value is commit_transactions in block;
# TYPE Node_Get_BlockDetail gauge
# HELP Node_Get_BlockDifference Get current bloack time and previous block time,label include CurrentHeight, PreviousHeight. value is Calculate the difference into seconds;
# TYPE Node_Get_BlockDifference gauge
Node_Get_BlockDifference{CurrentHeight="3892",GW_NODE_NAME="GW_NODE_ALPHA",PreviousHeight="3891",node_location="unknown"} 24457.0
# HELP Node_Get_BlockTimeDifference Get current bloack time and previous block time,value is Calculate the difference into seconds;
# TYPE Node_Get_BlockTimeDifference gauge
Node_Get_BlockTimeDifference{GW_NODE_NAME="GW_NODE_ALPHA",node_location="unknown"} 24457.0
```

ALl setup. Let prometheus starts to scrape.

## Docker

```shell
docker build -t godwoken-metrics-agent .
docker run -dp 3000:3000 --add-host=godwoken.web3:192.168.2.180 --env GW_NODE_NAME=godwoken godwoken-metrics-agent
```
