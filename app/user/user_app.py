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
RSK_DEST_ADDR = '0x8518266aCAe14073776De8371153A3389265d955'

class App:
    def __init__(self, log_file, q_name):
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

    def create_txn_id(self):
        u =  uuid.uuid4()  # Random 128 bits 
        return u.int
 
    def offchain_handshake(self, method, params):
        # With custodian
        txn_id = self.create_txn_id() 
        self.logger.info('Initiate %s, txn_id: %d' % (method, txn_id)) 
        js = {'jsonrpc' : '2.0', 'id' : txn_id, 
                  'method' : method, 'params' :  params}
        r = requests.post(CUSTODIAN_PORTAL_URL, json = js)
        self.logger.info(r.text)
        if r.status_code != requests.codes.ok:
            self.logger.error('Incorrect response code from custodian = %d' % 
                               r.status_code)
            return None, None
        return txn_id, json.loads(r.text)

    def run_fwd_txn(self, sbtc_amount): # sbtc->ebtc
        params = {'sbtc_amount' : sbtc_amount, 'user' : config.eth.user}
        txn_id, js = self.offchain_handshake('init_sbtc2ebtc', params)
        if txn_id is None: 
            return 1
 
        pwd_hash = js['result'] # of form '0x45667...'
        timeout_interval = 100 # Right timeout TBD
        self.logger.info('password hash from custodian = %s' % pwd_hash)

        # Wait for Custodian to transfer Ether To Ether contract
        self.logger.info('Waiting for custodian to transfer Ether to Ether contract')
        event_filter = self.eth_contract.events.FwdCustodianDeposited.createFilter(fromBlock = 'latest')
        event = self.w3_eth.wait_for_event(event_filter, txn_id)
        if event is None:  # Timeout 
            self.logger.info('Custodian did not respond. Quiting.')
            return 0 

        # Transfer SBTC to RSK contract
        self.logger.info('Depositing SBTC to RSK contract ..')
        self.rsk_tx['value'] = sbtc_amount
        tx_hash = self.rsk_concise.fwd_deposit(txn_id, 
                            self.w3_eth.w3.toBytes(hexstr = pwd_hash), 
                            timeout_interval, transact = self.rsk_tx) 

        self.w3_rsk.wait_to_be_mined(tx_hash) # TODO: Check for timeout
   
        # Wait for custodian to send password string on RSK 
        self.logger.info('Waiting for custodian to send password string')
        event_filter = self.rsk_contract.events.FwdCustodianExecutionSuccess.createFilter(fromBlock = 'latest')
        event = self.w3_rsk.wait_for_event(event_filter, txn_id)
        if event is None:  # Timeout
            self.logger.info('Customer did not send password string. Challenging..')
            tx_hash = self.rsk_concise.fwd_no_custodian_action_challenge(
                                                 txn_id, transact = self.rsk_tx)
            self.w3_rsk.wait_to_be_mined(tx_hash) # TODO: Check for timeout
            self.logger.info('Fwd transaction complete')
            return 0

        pwd_str = event['args']['pwd_str'] 

        # Issuing EBTC on Eth contract   
        self.logger.info('Issuing EBTC on Eth contract ..')
        tx_hash = self.eth_concise.fwd_issue(txn_id, pwd_str, 
                                             transact = self.eth_tx) 
        self.w3_eth.wait_to_be_mined(tx_hash)

        self.logger.info('Fwd transaction completed')
        return 0

    def run_rev_txn(self, ebtc_amount):
        # Headsup to custodian. TODO: This step is only there to trigger event
        # at the custodian's end. In deployment scenario this may not be 
        # needed, as custodian will be continuously watching events from
        # block chain 
 
        params = {'ebtc_amount' : ebtc_amount, 'user' : config.eth.user}
        txn_id, js = self.offchain_handshake('init_ebtc2sbtc', params)
        if txn_id is None: 
            return 1

        # TODO: Check if Id sent by custodian matches 
        # TODO: Ensure custodian has sufficient deposited Ether

        # Approve contract to transfer EBTC from user to contract 
        self.logger.info('Approving Contract to transfer EBTC from user')
        tx_hash = self.ebtc_concise.approve(config.eth.contract_addr, 
                                           int(10*1e18), transact = self.eth_tx)
        self.w3_eth.wait_to_be_mined(tx_hash)
 
        # Surrender EBTC
        self.logger.info('Surrendering %d EBTCs' % ebtc_amount)
        tx_hash = self.eth_concise.rev_request_redemption(txn_id, RSK_DEST_ADDR,
                                            ebtc_amount, transact = self.eth_tx) 
        self.w3_eth.wait_to_be_mined(tx_hash)

        # Wait for custodian to transfer SBTC to contract
        self.logger.info('Waiting for custodian to transfer SBTC to contract')
        event_filter = self.rsk_contract.events.RevCustodianDeposited.createFilter(fromBlock = 'latest')
        event = self.w3_rsk.wait_for_event(event_filter, txn_id)
        if event is None:  # Timeout
            self.logger.info('Customer did not deposit SBTC. Challenging ..')
            tx_hash = self.eth_concise.rev_no_custodian_action_challenge(txn_id,
                                                     transact = self.eth_tx) 
            self.w3_eth.wait_to_be_mined(tx_hash)
            self.logger.info('Rev Txn completed')
            return 0
        
        ack_hash = event['args']['ack_hash']  # Expected bytes
        self.logger.info('Hash = %s, type = %s' % (ack_hash, type(ack_hash)))
 
        # Send hash back to Ether contract 
        self.logger.info('Sending Hash to Eth contract ..')
        tx_hash = self.eth_concise.rev_add_hash(txn_id, pwd_hash, 
                                                 transact = self.eth_tx) 
        self.w3_eth.wait_to_be_mined(tx_hash)

        # Wait for password string from custodian 
        self.logger.info('Waiting for custodian to send password string..')
        event_filter = self.eth_contract.events.RevCustodianSecurityRecovered.createFilter(fromBlock = 'latest')
        event = self.w3_eth.wait_for_event(event_filter, txn_id)
        if event is None:  # Timeout
            self.logger.info('Customer did not send password. Challenging ..')
            tx_hash = self.eth_concise.rev_no_custodian_action_challenge(txn_id,
                                                     transact = self.eth_tx) 
            self.w3_eth.wait_to_be_mined(tx_hash)
            self.logger.info('Rev Txn completed')
            return 0
       
        ack_str = event['args']['ack_str']

        # Transfer SBTCs to destination address
        self.logger.info('Transfer SBTCs to destination address') 
        tx_hash = self.rsk_concise.rev_transfer(txn_id, ack_str, 
                                                transact = self.rsk_tx) 
        self.w3_rsk.wait_to_be_mined(tx_hash)

        self.logger.info('Rev Txn completed')
        return 0 

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
