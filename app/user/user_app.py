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

    def fwd_deposit(self, sbtc_amount):
        # Deposit SBTC to RSK contract
        self.logger.info('Depositing SBTC to RSK contract ..')
        self.rsk_tx['value'] = sbtc_amount
        txn_hash = self.rsk_concise.depositSBTC(config.eth.user, 
                                               transact = self.rsk_tx) 
        self.rsk_tx['value'] = 0
        self.logger.info('txn hash: %s' % HexBytes(txn_hash).hex())
        self.w3_rsk.wait_to_be_mined(txn_hash)

        self.logger.info('Wait for success log of above txn')
        event_filter = self.rsk_contract.events.UserDeposited.\
                           createFilter(fromBlock = 'latest')
        event = self.w3_rsk.wait_for_event(event_filter, txn_hash)
        return txn_hash
   
    def fwd_issue_ebtc(self, txn_hash_deposit):
        # Request EBTC issue on Eth
        js = json.dumps({"jsonrpc" : "2.0", "id" : 0, 
                         "method" : "eth_getTransactionByHash", 
                         "params" : "%s" % HexBytes(txn_hash_deposit).hex()})
        self.logger.info('Requesting issue of EBTC ..') 
        txn_hash = self.eth_concise.issueEBTC(txn_hash_deposit, js, 
                                              transact = self.eth_tx )
        self.w3_eth.wait_to_be_mined(txn_hash) 

        self.logger.info('Wait for EBTC issued event') 
        event_filter = self.eth_contract.events.EBTCIssued.\
                           createFilter(fromBlock = 'latest')
        event = self.w3_eth.wait_for_event(event_filter, None) 

    def rev_approve_ebtc(self):
        self.logger.info('Approve Eth contract to move EBTC')
        txn_hash = self.ebtc_concise.approve(config.eth.contract_addr, 
                                            10 * 10**18, 
                                            transact = self.eth_tx)
        self.logger.info('Tx hash: %s' % HexBytes(txn_hash).hex())
        self.w3_eth.wait_to_be_mined(txn_hash) 

    def rev_redeem_ebtc(self, ebtc_amount):
        self.logger.info('Surrending EBTC ..')   
        txn_hash = self.eth_concise.redeem(config.rsk.dest_addr, ebtc_amount,
                                           transact = self.eth_tx)
        self.w3_eth.wait_to_be_mined(txn_hash) 

        self.logger.info('Wait for EBTCSurrendered event')
        event_filter = self.eth_contract.events.EBTCSurrendered.\
                           createFilter(fromBlock = 'latest')
        event = self.w3_eth.wait_for_event(event_filter, txn_hash) 
        return txn_hash

    def rev_redeem_sbtc(self, txn_hash_redeem):     
        self.logger.info('Redeeming SBTC..')
      
        js = json.dumps({"jsonrpc" : "2.0", "id" : 0, 
                         "method" : "eth_getTransactionByHash", 
                         "params" : "%s" % HexBytes(txn_hash_redeem).hex()})
        txn_hash = self.rsk_concise.redeem(txn_hash_redeem, js, 
                                           transact = self.rsk_tx)
        self.w3_rsk.wait_to_be_mined(txn_hash) 

        self.logger.info('Wait for UserRedeemed event') 
        event_filter = self.rsk_contract.events.UserRedeemed.\
                           createFilter(fromBlock = 'latest')
        event = self.w3_rsk.wait_for_event(event_filter, None) 

    def run_fwd_txn(self, sbtc_amount): # sbtc->ebtc
        txn_hash = self.fwd_deposit(sbtc_amount) 

        # Wait for at least 2 blocks  
        bn = self.w3_rsk.w3.eth.blockNumber
        self.logger.info('Waiting for enough confirmations')       
        while (self.w3_rsk.w3.eth.blockNumber - bn) <=2:
            time.sleep(2)

        self.fwd_issue_ebtc(txn_hash)

    def run_rev_txn(self, ebtc_amount):
        #self.rev_approve_ebtc()

        #txn_hash = self.rev_redeem_ebtc(ebtc_amount) 

        # Wait for at least 2 blocks  
        '''
        bn = self.w3_eth.w3.eth.blockNumber
        self.logger.info('Waiting for enough confirmations')       
        while (self.w3_eth.w3.eth.blockNumber - bn) <=2:
            time.sleep(2)
        '''

        txn_hash = HexBytes('0x30ed16405e1c15c037504458d235122e5153db36bb5c3923f726720436ba8a3a')
        self.rev_redeem_sbtc(txn_hash)

def main():
    if len(sys.argv) != 3:
        print('Usage: python user_app.py <fwd | rev>  <sbtc | ebtc amount in float>')
        exit(0)
    
    wei = int(float(sys.argv[2]) * 1e18) # In Wei
    app = App('/tmp/stride.log')
    if sys.argv[1] == 'fwd':
        app.run_fwd_txn(wei)
    elif sys.argv[1] == 'rev':
        app.run_rev_txn(wei)
    else:
        print('Invalid argument')
        exit(0)

if __name__== '__main__':
    main()
