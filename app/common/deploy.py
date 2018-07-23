# Author: Bon Filey (bonfiley@gmail.com)
# Copyright 2018 Bromley Labs Inc.

from web3 import Web3
from hexbytes import HexBytes
import sys
from common.utils import * 
from common import config

def main():
    if len(sys.argv) != 3:
        print('Usage: python deploy.py <rsk | eth> <contract_name>')
        exit(0)

    logger = init_logger('DEPLOY', '/tmp/stride.log')
    if sys.argv[1] == 'rsk':
        chain = W3Utils(config.rsk, logger)
    elif sys.argv[1] == 'eth':
        chain = W3Utils(config.eth, logger)
    else:
        printf('Incorrect argument')

    status, tx_receipt = chain.deploy(sys.argv[2])
    logger.info('Contact address = %s' % tx_receipt['contractAddress'])

if __name__== '__main__':
    main()
