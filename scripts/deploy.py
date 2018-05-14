from web3 import Web3
from hexbytes import HexBytes
import sys
from utils import *
import utils
import config

def main():
    if len(sys.argv) != 2:
        print('Usage: python deploy.py <rsk | eth>')
        exit(0)

    logger = init_logger('DEPLOY')
    if sys.argv[1] == 'rsk':
        chain = W3Utils(config.rsk, logger)
    elif sys.argv[1] == 'eth':
        chain = W3Utils(config.eth, logger)
    else:
        printf('Incorrect argument')

    tx_receipt = chain.deploy() 
    logger.info('Contact address = %s' % tx_receipt['contractAddress']

if __name__== '__main__':
    main()
