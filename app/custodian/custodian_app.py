# This daemon will run by customer at his premises or in his control. 

import json
from pymongo import MongoClient
import datetime
from common import config
from common.utils import *
import threading
import copy

ETH_EBTC_RATIO = 15.0

class App:
    def __init__(self, log_file, q_name):
        self.event_q = RabbitMQ(q_name)
        self.event_q.channel.basic_consume(self.callback, queue=q_name,
                                           no_ack=True)
        self.logger = init_logger('CUST',  log_file)
        self.db_client = MongoClient() # Default location 
        self.db = self.db_client['custodian-db']
        self.collection = self.db['transactions'] 
        self.w3_rsk = W3Utils(config.rsk, self.logger)
        self.w3_eth = W3Utils(config.eth, self.logger)
        self.eth_contract, self.eth_concise = self.w3_eth.init_contract('StrideEthContract', config.eth.contract_addr) 
        self.rsk_contract, self.rsk_concise = self.w3_rsk.init_contract('StrideRSKContract', config.rsk.contract_addr) 
        # For convenience:
        self.eth_tx = {'from' : config.eth.custodian, 'gas' : config.eth.gas, 
                       'gasPrice' : config.eth.gas_price, 'value' : 0} 
        self.rsk_tx = {'from' : config.rsk.custodian, 'gas' : config.rsk.gas, 
                       'gasPrice' : config.rsk.gas_price, 'value' : 0} 
        
    def start(self):
        self.logger.info('Listening to events ..')
        self.event_q.channel.start_consuming()

    def callback(self, ch, method, properties, body):
        msg = str(body, 'utf-8') # body type is bytes (for some reason)
        self.logger.info('Received: %s' % msg)   
        msg = json.loads(msg)
        if msg['method'] == 'init_sbtc2ebtc':
            func = self.run_fwd_txn
        if msg['method'] == 'init_ebtc2sbtc':
            func = self.run_rev_txn

        th = threading.Thread(target = func, args=(msg,)) 
        th.daemon = True
        th.start()
        self.logger.info('%s thread forked' % func)

    def insert_in_db(self, msg):
        # Convert long int to str for db write 
        m = copy.deepcopy(msg) 
        m['id'] = str(m['id'])
        if 'sbtc_amount' in m['params']:
            m['params']['sbtc_amount'] = str(m['params']['sbtc_amount'])
        if 'ebtc_amount' in m['params']:
            m['params']['ebtc_amount'] = str(m['params']['ebtc_amount'])
        self.collection.insert_one(m)
        self.logger.info('msg saved in DB')

    def run_fwd_txn(self, msg): # sbtc->ebtc
        # msg is {}
        self.insert_in_db(msg)

        txn_id = msg['id']
        pwd_hash = msg['pwd_hash']  # Hex string '0x..'
        pwd_str = msg['pwd_str']
        user_eth = msg['params']['user'] 
        ebtc_amount = msg['params']['sbtc_amount']
        timeout_interval = 100 # Arbitrary
        eth_amount = int(ETH_EBTC_RATIO * ebtc_amount)
        
        '''
        # Deposit collateral to Eth contract
        self.logger.info('Depositing Ether to contract..')
        self.eth_tx['value'] = eth_amount # Payable method
        tx_hash = self.eth_concise.fwd_deposit(txn_id, user_eth, 
                     self.w3_eth.w3.toBytes(hexstr = pwd_hash), 
                     timeout_interval, ebtc_amount, transact = self.eth_tx) 
        self.eth_tx['value'] = 0 # Reset 
        self.w3_eth.wait_to_be_mined(tx_hash) # TODO: check for timeout
        '''

        # Wait for user to deposit SBTC on RSK 
        self.logger.info('Waiting for user to deposit SBTC on RSK')  
        event_filter = self.rsk_contract.events.FwdUserDeposited.createFilter(fromBlock = 'latest')
        event = self.w3_rsk.wait_for_event(event_filter, txn_id, 
                                           timeout_interval)
        if event is None:  # Timeout. 
            self.logger.info('Challenge ..')
            tx_hash = self.eth_concise.fwd_no_user_action_challenge(txn_id,
                                                      transact = self.eth_tx) 
            self.w3_eth.wait_to_be_mined(tx_hash)
            self.logger.info('Fwd transaction completed')
            return 0
         
        # Send pwd str to user
        self.logger.info('Transferring SBTC to custodian addr on RSK') 
        tx_hash = self.rsk_concise.fwd_transfer(txn_id, pwd_str, 
                                                transact = self.rsk_tx) 
        self.w3_rsk.wait_to_be_mined(tx_hash)

        self.logger.info('Forward transaction completed') 
        return 0

    def run_rev_txn(self, msg): # ebtc->sbtc
        # msg is {}
        self.insert_in_db(msg)
        self.logger.info('Inserted in DB')
        
        # Offchain msg from user
        txn_id = msg['id']
        user_eth = msg['params']['user'] 
        ebtc_amount = msg['params']['ebtc_amount']
        timeout_interval = 100 # Arbitrary

        # Check if enough Ether is there on contract, otherwise send
        # TODO: Check for locked ether and then calculate 
        eth_amount = int(ETH_EBTC_RATIO * ebtc_amount)
        self.logger.info('Sending collateral Ether to contract')
        self.eth_tx['value'] = eth_amount # Payable method
        tx_hash = self.eth_concise.consume_eth(transact = self.eth_tx) 
        self.eth_tx['value'] = 0 # Reset
        self.w3_eth.wait_to_be_mined(tx_hash)

        # Wait for User to surrender EBTCs on Eth contract
        self.logger.info('Waiting for user to surrender EBTCs ..')
        event_filter = self.eth_contract.events.RevRedemptionInitiated.createFilter(fromBlock = 'latest')
        event = self.w3_eth.wait_for_event(event_filter, txn_id, timeout_interval)
        if event is None:  # Timeout. 
            self.logger.info('No redemption request from user')
            self.logger.info('Rev Txn aborting') 
            return 0
        
        dest_addr = event['args']['dest_rsk_addr']
        self.logger.info('RSK distination address: %s' % dest_addr)
        # TODO: User RSK address must also be read from the offchain initiation 
        # message sent by the user.  Right now, picking it up from config.

        # Deposit SBTCs on RSK contract and pass on a hash
        self.logger.info('Depositing SBTCs on RSK ..')
        pwd_str, pwd_hash = self.w3_eth.generate_random_string(4)
        self.logger.info('Generate pwd: %s, hash = %s' % (pwd_str, pwd_hash.hex()))
        self.rsk_tx['value'] = ebtc_amount
        tx_hash = self.rsk_concise.rev_deposit(txn_id, config.rsk.user,
                                               dest_addr, ebtc_amount, 
                               self.w3_rsk.w3.toBytes(hexstr = pwd_hash.hex()), 
                                               transact = self.rsk_tx)
        self.rsk_tx['value'] = 0 # Reset
        self.w3_rsk.wait_to_be_mined(tx_hash)
      
        # Waiting for hash from user
        self.logger.info('Waiting for hash from user..')
        event_filter = self.eth_contract.events.RevHashAdded.createFilter(fromBlock = 'latest')
        event = self.w3_eth.wait_for_event(event_filter, txn_id, timeout_interval)
        if event is None:  # Timeout. 
            self.logger.info('No action by user. Challenging ..')
            self.logger.info('Get back SBTCs on RSK ..')
            tx_hash = self.rsk_concise.rev_challenge(txn_id,
                                                 transact = self.rsk_tx)
            self.w3_rsk.wait_to_be_mined(tx_hash)

            self.logger.info('Get back collateral eth on Eth ..')
            tx_hash = self.eth_concise.rev_no_user_action_challenge(txn_id,
                                                 transact = self.eth_tx)
            self.w3_eth.wait_to_be_mined(tx_hash)
            self.logger.info('Rev txn complete')
            return 0

        # TODO: Verify hash 
        if event['args']['ack_hash'] != self.w3_eth.w3.toBytes(hexstr = pwd_hash.hex()): 
            self.logger.error('Hashes do not match: %s, %s' % (event['args']['ack_hash'], self.w3_eth.w3.toBytes(hexstr = pwd_hash.hex()))) 
        else:
            self.logger.info('Hashes match')

        # Recover security deposit
        self.logger.info('Recovering security deposit ..')
        tx_hash = self.eth_concise.rev_recover_security_deposit(txn_id, pwd_str, transact = self.eth_tx)
        self.w3_eth.wait_to_be_mined(tx_hash)

        self.logger.info('Rev txn complete')
        return 0

def main():
    app = App('/tmp/stride.log', 'custodian-q')
    app.start()

if __name__== '__main__':
    main()
