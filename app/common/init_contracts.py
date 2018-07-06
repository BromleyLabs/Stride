# This script functions to be called once all contracts have been fresh 
# deployed.  The functions here set various member variables needed for 
# executing transactions. Would need to run this script only once after 
# all contracts are uploaded.

from web3 import Web3
from hexbytes import HexBytes
import sys
from common.utils import * 
from common import config

class App:
    def __init__(self, log_file):
        self.logger = init_logger('DEPLOY', log_file) 
        self.rsk = W3Utils(config.rsk, self.logger)
        self.eth = W3Utils(config.eth, self.logger)
        self.eth_tx = {'from' : config.eth.contract_owner, 
                        'gas' : config.eth.gas, 
                        'gasPrice' : config.eth.gas_price} # Convenience 
        self.rsk_tx = {'from' : config.rsk.contract_owner, 
                       'gas' : config.rsk.gas, 
                       'gasPrice' : config.rsk.gas_price} # Convenience 
         
        _, self.eth_concise = self.eth.init_contract('StrideEthContract',
                                                      config.eth.contract_addr) 
        _, self.rsk_concise = self.rsk.init_contract('StrideRSKContract', 
                                                     config.rsk.contract_addr) 
        _, self.ebtc_concise = self.eth.init_contract('EBTCToken', 
                                                       config.eth.token_addr)

    def set_eth_contract_addr_on_rsk(self): 
        self.logger.info('Setting Eth contract address on RSK Contract') 
        return self.rsk_concise.set_eth_contract_addr(config.eth.contract_addr,
                                                     transact = self.rsk_tx) 
    def set_eth_proof_contract_addr_on_rsk(self): 
        self.logger.info('Setting EthProof contract address on RSK Contract') 
        return self.rsk_concise.set_eth_proof_addr(
                   config.eth_proof_contract_addr, transact = self.rsk_tx) 

    def set_ebtc_token_addr_on_eth(self):
        self.logger.info('Setting EBTC Token address on Eth Contract') 
        return self.eth_concise.set_ebtc_token_address(config.eth.token_addr,
                                                       transact = self.eth_tx) 
    def set_issuer_on_ebtc_token(self):
        self.logger.info('Setting m_issuer on Token address on Eth Contract') 
        return self.ebtc_concise.setIssuer(config.eth.contract_addr,
                                              transact = self.eth_tx) 

    def set_min_confirmations_on_rsk(self, n):
        self.logger.info('Set min confirmation on RSK')
        return self.rsk_concise.set_min_confirmations(n, 
                                                      transact = self.rsk_tx) 

    def set_custodian_on_rsk(self):
        self.logger.info('Set custodian on RSK') 
        return self.rsk_concise.set_custodian(config.rsk.custodian, 
                                              transact = self.rsk_tx) 

    def set_custodian_on_eth(self):
        self.logger.info('Set custodian on Eth') 
        return self.eth_concise.set_custodian(config.eth.custodian, 
                                              transact = self.eth_tx) 

if __name__== '__main__':
    if len(sys.argv) != 1:
        print('Usage: python init_contracts.py')
        exit(0)

    app = App('/tmp/stride.log')
    
    '''
    # Rsk
    rsk_txns = [] 
    txn = app.set_eth_contract_addr_on_rsk()
    rsk_txns.append(txn)

    txn =  app.set_eth_proof_contract_addr_on_rsk()
    rsk_txns.append(txn)

    txn = app.set_min_confirmations_on_rsk(1) # Only for testing
    rsk_txns.append(txn)

    txn = app.set_custodian_on_rsk()
    rsk_txns.append(txn)

    app.rsk.wait_to_be_mined_batch(rsk_txns)

    '''
    #Eth
    eth_txns = []

    txn = app.set_custodian_on_eth()
    eth_txns.append(txn)

    txn = app.set_issuer_on_ebtc_token()
    eth_txns.append(txn)

    txn = app.set_ebtc_token_addr_on_eth()
    eth_txns.append(txn)

    app.eth.wait_to_be_mined_batch(eth_txns)


