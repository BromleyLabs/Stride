# This script functions to be called once all contracts have been fresh 
# deployed.  The functions here set various member variables needed for 
# executing transactions. Would need to run this script only once after 
# all contracts are uploaded.

from web3 import Web3
from hexbytes import HexBytes
import sys
from common.utils import * 
from common import config

RSK_DEST_ADDR = '0x8518266aCAe14073776De8371153A3389265d955'
def main():

    logger = init_logger('SCAN', '/tmp/stride.log')

    rsk = W3Utils(config.rsk, logger)
    eth = W3Utils(config.eth, logger)
     
    print('RSK User: %.10f' % (rsk.w3.eth.getBalance(config.rsk.user) / 1e18))
    print('RSK Custodian: %.10f' % (rsk.w3.eth.getBalance(config.rsk.custodian) / 1e18))
    print('RSK Destination: %.10f' % (rsk.w3.eth.getBalance(RSK_DEST_ADDR) / 1e18))
    print('RSK Contract: %.10f' % (rsk.w3.eth.getBalance(config.rsk.contract_addr) / 1e18))

    print('Eth User: %.10f' % (eth.w3.eth.getBalance(config.eth.user) / 1e18))
    print('Eth Custodian: %.10f' % (eth.w3.eth.getBalance(config.eth.custodian) / 1e18))
    print('Eth Contract: %.10f' % (eth.w3.eth.getBalance(config.eth.contract_addr) / 1e18))


if __name__== '__main__':
   main()
