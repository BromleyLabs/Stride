# This daemon will run by customer at his premises or in his control. 
import sys
import uuid
import json
from pymongo import MongoClient
import datetime
from common import config
from common.utils import *
import requests

class App:
    def __init__(self, log_file):
        self.logger = init_logger('USER',  log_file)
        self.w3_rsk = W3Utils(config.rsk, self.logger)
        self.w3_eth = W3Utils(config.eth, self.logger)
        self.eth_contract, self.eth_concise = self.w3_eth.init_contract(
                                 'StrideEthContract', config.eth.contract_addr) 
        self.rsk_contract, self.rsk_concise = self.w3_rsk.init_contract(
                                 'StrideRSKContract', config.rsk.contract_addr) 
        self.ebtc_contract, self.ebtc_concise = self.w3_eth.init_contract(
                                 'EBTCToken', config.eth.token_addr) 
        
        self.eth_tx = {'from' : config.eth.user, 'gas' : config.eth.gas, 
                       'gasPrice' : config.eth.gas_price, 'value' : 0}
        self.rsk_tx = {'from' : config.rsk.user, 'gas' : config.rsk.gas, 
                       'gasPrice' : config.rsk.gas_price, 'value' : 0} 


    def run_fwd_txn(self, sbtc_amount): # sbtc->ebtc
        '''
        # Deposit SBTC to RSK contract
        self.logger.info('Depositing SBTC to RSK contract ..')
        self.rsk_tx['value'] = sbtc_amount
        txn_hash = self.rsk_concise.depositSBTC(config.eth.user, 
                                               transact = self.rsk_tx) 
        self.logger.info('txn_hash: %s' % txn_hash)
        self.w3_rsk.wait_to_be_mined(txn_hash) # TODO: Check for timeout
        self.logger.info('Wait for success log of above txn')
        event_filter = self.rsk_contract.events.UserDeposited.\
                           createFilter(fromBlock = 'latest')
        event = self.w3_rsk.wait_for_event(event_filter, txn_hash)

        '''
        txn_hash_deposit = '0xcae079107bebd6036cb5e45339c0876196460f5c11973f0f94450e85e430f2e8'
        # Request EBTC issue on Eth
        js = json.dumps({"jsonrpc" : "2.0", "id" : 0, 
                         "method" : "eth_getTransactionByHash", 
                         "params" : ["%s" % txn_hash_deposit]})
        self.logger.info('Requesting issue of EBTC ..') 
        hash_bytes = self.w3_eth.w3.toBytes(hexstr = txn_hash_deposit) 
        txn_hash = self.eth_concise.issueEBTC(hash_bytes, js, 
                                              transact = self.eth_tx )
        self.w3_eth.wait_to_be_mined(txn_hash) # TODO: Check for timeout

        self.logger.info('Wait for EBTC issued event') 
        event_filter = self.eth_contract.events.EBTCIssued.\
                           createFilter(fromBlock = 'latest')
        event = self.w3_eth.wait_for_event(event_filter, None) 

def main():
    if len(sys.argv) != 3:
        print('Usage: python user_app.py <fwd | rev>  <sbtc | ebtc amount in float>')
        exit(0)
    
    wei = int(float(sys.argv[2]) * 1e18) # In Wei
    app = App('/tmp/stride.log')
    if sys.argv[1] == 'fwd':
        app.run_fwd_txn(wei)
    else:
        print('Invalid argument')
        exit(0)

if __name__== '__main__':
    main()
