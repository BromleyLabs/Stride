#!/bin/bash

SOLC_PATH=/usr/bin
OPTIONS="--bin --abi --optimize --opcodes --overwrite"
rm -rf target
$SOLC_PATH/solc -o target $OPTIONS stride_eth.sol stride_rsk.sol eth_proof.sol 

