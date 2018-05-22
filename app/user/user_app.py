# This daemon will run by customer at his premises or in his control. 
import sys
import uuid
import json
from pymongo import MongoClient
import datetime
from common import config
from common.utils import *
import requests

CUSTODIAN_PORTAL_URL = 'http://localhost:5000/stride'

class App:
    def __init__(self, log_file, q_name):
        self.logger = init_logger('USER',  log_file)
        self.w3_rsk = W3Utils(config.rsk, self.logger)
        self.w3_eth = W3Utils(config.eth, self.logger)
        self.eth_contract, self.eth_consise = self.w3_eth.init_contract('StrideEthContract') 
        self.rsk_contract, self.rsk_consise = self.w3_eth.init_contract('StrideRSKContract') 
        self.eth_tx = {'from' : config.eth.user, 'gas' : config.eth.gas, 'gasPrice' : config.eth.gasPrice} # Convenience 
        self.rsk_tx = {'from' : config.rsk.user, 'gas' : config.rsk.gas, 'gasPrice' : config.rsk.gasPrice} # Convenience 

    def run_fwd_txn(self, amount): # sbtc->ebtc
        self.logger.info('Initiate txn')
        u =  uuid.uuid4()  # Random 128 bits 
        txn_id = u.int 
        self.logger.info('Txn Id: %d' % txn_id) 
        js = {'jsonrpc' : '2.0', 'id' : txn_id, 'method' : 'init_sbtc2ebtc', 
              'params' : {'sbtc_amount' : amount, 'user' : config.eth.user}}
        r = requests.post(CUSTODIAN_PORTAL_URL, json = js)
        self.logger.info(r.text)
        if r.status_code != requests.codes.ok:
            self.logger.error('Incorrect response code from custodian = %d' % 
                               r.status_code)
            return 1
        js = json.loads(r.text)
        pwd_hash = js['result'] # of form '0x45667...'
        logger.info('password hash from custodian = %s' % pwd_hash)

        # Wait for Custodian to transfer EBTC To Ether contract
        logger.info('Waiting for custodian to transfer EBTC to Ether contract')
        event_filter = self.eth_contract.contract.events.FwdCustodianDeposited.createFilter(fromBlock = 'latest')
        self.w3_eth.wait_for_event(event_filter, txn_id)
          
        # Transfer SBTC to RSK contract
        tx_hash = self.rsk_concise.fwd_deposit(txn_id, pwd_hash, 200, 
                                               transact = self.eth_tx) 
        self.w3_rsk.wait_to_be_mined(tx_hash)
        

    def run_rev_txn(self, amount):
        pass
    
        # TODO: For first few steps of Atomic Swap custodian must verify that
        # the txn_id being used by the user for contract is same as what 
        # custodian has in DB, otherwise, pwd hash may not match

def main():
    if len(sys.argv) != 3:
        print('Usage: python user_app.py <fwd | rev>  <sbtc | ebtc amount in float>')
        exit(0)
    
    wei = int(float(sys.argv[2]) * 1e18) # In Wei
    app = App('/tmp/stride.log', 'custodian-q')
    if sys.argv[1] == 'fwd':
        app.run_fwd_txn(wei)
    elif sys.argv[1] == 'rev':
        app.run_rev_txn(wei)
    else:
        print('Invalid argument')
        exit(0)

if __name__== '__main__':
    main()
