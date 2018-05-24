# This script functions to be called once all contracts have been fresh 
# deployed.  The functions here set various member variables needed for 
# executing transactions. Would need to run this script only once after 
# all contracts are uploaded.

from web3 import Web3
from hexbytes import HexBytes
import sys
from common.utils import * 
from common import config

def main():

    logger = init_logger('SCAN', '/tmp/stride.log')

    rsk = W3Utils(config.rsk, logger)
    eth = W3Utils(config.eth, logger)
     
    print('RSK User: %f' % (rsk.w3.eth.getBalance(config.rsk.user) / 1e18))
    print('RSK Custodian: %f' % (rsk.w3.eth.getBalance(config.rsk.custodian) / 1e18))
    print('RSK Contract: %f' % (rsk.w3.eth.getBalance(config.rsk.contract_addr) / 1e18))

    print('Eth User: %f' % (eth.w3.eth.getBalance(config.eth.user) / 1e18))
    print('Eth Custodian: %f' % (eth.w3.eth.getBalance(config.eth.custodian) / 1e18))
    print('Eth Contract: %f' % (eth.w3.eth.getBalance(config.eth.contract_addr) / 1e18))


if __name__== '__main__':
   main()
