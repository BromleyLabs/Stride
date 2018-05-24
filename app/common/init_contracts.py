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

    # Set custodian 
    logger.info('Setting custodian on RSK ..') 
    tx_hash = rsk_concise.set_custodian(config.rsk.custodian,
                                             transact = rsk_tx) 
    rsk.wait_to_be_mined(tx_hash)

    logger.info('Setting custodian on Eth ..') 
    tx_hash = eth_concise.set_custodian(config.eth.custodian,
                                             transact = eth_tx) 
    eth.wait_to_be_mined(tx_hash)

    # Set lock interval
    logger.info('Setting lock interval on RSK ..')
    tx_hash = rsk_concise.set_lock_interval(100, transact = rsk_tx) 
    rsk.wait_to_be_mined(tx_hash)
    
    logger.info('Setting lock interval on ETH ..')
    tx_hash = eth_concise.set_lock_interval(100, transact = eth_tx) 
    eth.wait_to_be_mined(tx_hash)
    # Set EBTC Token address 
    logger.info('Setting EBTC token address on Eth ..')
    tx_hash = eth_concise.set_ebtc_token_address(config.eth.token_addr,
                                                      transact = eth_tx) 
    eth.wait_to_be_mined(tx_hash)

    # Set ETH/EBTC ratio
    logger.info('Setting ETH/EBTC ration on Eth ..')
    tx_hash = eth_concise.set_eth_ebtc_ratio(15, 1, transact = eth_tx)
    eth.wait_to_be_mined(tx_hash)

    # Set issuer of EBTC token
    logger.info('Setting Issuer address on Eth ..')
    tx_hash = ebtc_concise.setIssuer(config.eth.contract_addr, 
                                     transact = eth_tx)
    eth.wait_to_be_mined(tx_hash)


if __name__== '__main__':
    main()
