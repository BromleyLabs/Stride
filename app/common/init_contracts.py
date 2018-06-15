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
        txn_hash = self.rsk_concise.setEthContractAddr(config.eth.contract_addr,
                                                     transact = self.rsk_tx) 
        self.rsk.wait_to_be_mined(txn_hash)

    def set_rsk_contract_addr_on_eth(self):
        self.logger.info('Setting RSK contract address on Eth Contract') 
        txn_hash = self.eth_concise.setRSKContractAddr(config.rsk.contract_addr,
                                                      transact = self.eth_tx) 
        self.eth.wait_to_be_mined(txn_hash)

    def set_ebtc_token_addr_on_eth(self):
        self.logger.info('Setting EBTC Token address on Eth Contract') 
        txn_hash = self.eth_concise.setEBTCTokenAddress(config.eth.token_addr,
                                                       transact = self.eth_tx) 
        self.eth.wait_to_be_mined(txn_hash)

    def set_issuer_on_ebtc_token(self):
        self.logger.info('Setting m_issuer on Token address on Eth Contract') 
        txn_hash = self.ebtc_concise.setIssuer(config.eth.contract_addr,
                                              transact = self.eth_tx) 
        self.eth.wait_to_be_mined(txn_hash)
    
    def set_server_url_on_eth(self):
        self.logger.info('Setting the server URL on Eth')
        txn_hash = self.eth_concise.setStrideServerURL("binary(https://stride.ddns.net/stride/rsk/testnet).slice(0, 136)", transact = self.eth_tx) 
        self.eth.wait_to_be_mined(txn_hash)
     
    def set_server_url_rsk(self):
       self.logger.info('Setting the server URL on RSK')
       txn_hash = self.rsk_concise.setStrideServerURL("binary(https://stride.ddns.net/stride/ethereum/ropsten).slice(0, 136)", transact = self.rsk_tx) 
       self.rsk.wait_to_be_mined(txn_hash)

    def transfer_ether_from_user_to_eth(self, wei):
        self.logger.info('Transfer some Eth to Eth contract for Oraclize')
        txn_hash = self.eth.w3.eth.sendTransaction({
            'from': config.eth.user, 
            'to': config.eth.contract_addr,
            'value' : wei 
            }
        )
        self.logger.info('Tx hash: %s' % HexBytes(txn_hash).hex())
   
    def transfer_sbtc_from_user_to_rsk(self, wei):
        self.logger.info('Transfer some SBTC to RSK contract for Oraclize')
        txn_hash = self.rsk.w3.eth.sendTransaction({
            'from' : config.rsk.user, 
            'to': config.rsk.contract_addr,
            'value' : wei 
            }
        )
        self.logger.info('Tx hash: %s' % HexBytes(txn_hash).hex())

    def set_min_confirmations_on_rsk(self, n):
        self.logger.info('Set Min confirmation on RSK')
        txn_hash = self.rsk_concise.setMinConfirmations(n, 
                                                        transact = self.rsk_tx) 
        self.rsk.wait_to_be_mined(txn_hash)

    def set_min_confirmations_on_eth(self, n):
        self.logger.info('Set Min confirmation on Eth')
        txn_hash = self.eth_concise.setMinConfirmations(n, 
                                                        transact = self.eth_tx) 
        self.eth.wait_to_be_mined(txn_hash)
    

if __name__== '__main__':
    if len(sys.argv) != 1:
        print('Usage: python init_contracts.py')
        exit(0)

    app = App('/tmp/stride.log')
    
    # Rsk
    #app.set_eth_contract_addr_on_rsk()
    #app.set_min_confirmations_on_rsk(1) # Only for testing
    #app.transfer_sbtc_from_user_to_rsk(int(0.0001 * 10**18))

    #Eth
    #app.set_rsk_contract_addr_on_eth() # Only for testing
    app.set_min_confirmations_on_eth(1)
    #app.transfer_ether_from_user_to_eth(int(0.0001 * 10**18))
    #app.set_ebtc_token_addr_on_eth()
