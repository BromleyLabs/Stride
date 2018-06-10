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
    if len(sys.argv) != 1:
        print('Usage: python init_contracts.py')
        exit(0)

    logger = init_logger('DEPLOY', '/tmp/stride.log')
    rsk = W3Utils(config.rsk, logger)
    eth = W3Utils(config.eth, logger)
    eth_tx = {'from' : config.eth.contract_owner, 'gas' : config.eth.gas, 
              'gasPrice' : config.eth.gas_price} # Convenience 
    rsk_tx = {'from' : config.rsk.contract_owner, 'gas' : config.rsk.gas, 
              'gasPrice' : config.rsk.gas_price} # Convenience 
     
    eth_contract, eth_concise = eth.init_contract('StrideEthContract',
                                                      config.eth.contract_addr) 
    rsk_contract, rsk_concise = rsk.init_contract('StrideRSKContract', 
                                                      config.rsk.contract_addr) 
    ebtc_contract, ebtc_concise = eth.init_contract('EBTCToken', 
                                                        config.eth.token_addr)

    logger.info('Setting Eth contract address on RSK Contract') 
    tx_hash = rsk_concise.setEthContractAddr(config.eth.contract_addr,
                                             transact = rsk_tx) 
    rsk.wait_to_be_mined(tx_hash)

    logger.info('Setting RSK contract address on Eth Contract') 
    tx_hash = eth_concise.setRSKContractAddr(config.rsk.contract_addr,
                                             transact = eth_tx) 
    eth.wait_to_be_mined(tx_hash)

    logger.info('Setting EBTC Token address on Eth Contract') 
    tx_hash = eth_concise.setEBTCTokenAddress(config.eth.token_addr,
                                           transact = eth_tx) 
    eth.wait_to_be_mined(tx_hash)


if __name__== '__main__':
    main()
