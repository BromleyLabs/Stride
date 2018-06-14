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
     
    path = os.path.join(config.eth.contract_path, 'EBTCToken.abi')
    abi = open(path, 'rt').read()
    ebtc = eth.w3.eth.contract(abi = abi, address = config.eth.token_addr) 

    print('RSK User SBTC: %.10f' % (rsk.w3.eth.getBalance(config.rsk.user) / 1e18))
    print('RSK Destination SBTC: %.10f' % (rsk.w3.eth.getBalance(config.rsk.dest_addr) / 1e18))
    print('RSK Contract SBTC: %.10f' % (rsk.w3.eth.getBalance(config.rsk.contract_addr) / 1e18))

    print('ETH User Ether: %.10f' % (eth.w3.eth.getBalance(config.eth.user) / 1e18))
    print('ETH Contract Ether: %.10f' % (eth.w3.eth.getBalance(config.eth.contract_addr) / 1e18))

    print('ETH User EBTC: %.10f' % (ebtc.functions.balanceOf(config.eth.user).call() / 1e18))
    print('ETH Contract EBTC: %.10f' % (ebtc.functions.balanceOf(config.eth.contract_addr).call() / 1e18))
    
    

if __name__== '__main__':
   main()
