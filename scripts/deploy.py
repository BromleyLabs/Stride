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
    utils.logger = logger
 
    if sys.argv[1] == 'rsk':
        chain = config.rsk 
    elif sys.argv[1] == 'eth':
        chain = config.eth
    else:
        print('Incorrect chain specified')
        exit(0)

    w3 = Web3(Web3.HTTPProvider(chain.rpc_addr))
    utils.w3 = w3
    if chain == config.rsk: 
        unlock_accounts([chain.contract_owner], "puneet")
    # For Parity start parity node with unlocked accounts 
    tx_receipt = deploy(chain)
    logger.info('Contract address = %s' % tx_receipt['contractAddress']

if __name__== '__main__':
    main()
