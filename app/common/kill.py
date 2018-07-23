# Kill a given contract on either RSK or ETH 
#
# Author: Bon Filey (bonfiley@gmail.com)
# Copyright 2018 Bromley Labs Inc.

import sys
from web3 import Web3
from hexbytes import HexBytes
import sys
from common.utils import * 
from common import config

def main():
    if len(sys.argv) != 4:
        print('Usage: python kill.py <rsk|eth> <contract name>, <contract addresss>')  
        exit(0)

    contract_name = sys.argv[2]
    contract_addr = sys.argv[3]

    logger = init_logger('KILL', '/tmp/stride.log')
    if sys.argv[1] == 'rsk':
        chain = W3Utils(config.rsk, logger)
        conf = config.rsk
    elif sys.argv[1] == 'eth':
        chain = W3Utils(config.eth, logger)
        conf = config.eth
    else:
        print('Incorrect chain argument')
        return 0
     
    tx = {'from' : conf.contract_owner, 'gas' : conf.gas, 
          'gasPrice' : conf.gas_price} 
    contract, concise = chain.init_contract(contract_name, contract_addr) 

    # Set custodian 
    logger.info('Killing %s' % contract_name)
    tx_hash = concise.kill(transact = {'from' : conf.contract_owner, 
                                       'gas' : conf.gas, 
                                       'gasPrice' : conf.gas_price}) 
    chain.wait_to_be_mined(tx_hash)


if __name__== '__main__':
    main()
