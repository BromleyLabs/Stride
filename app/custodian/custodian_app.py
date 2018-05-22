# This daemon will run by customer at his premises or in his control. 

import json
from pymongo import MongoClient
import datetime
from common import config
from common.utils import *

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
        self.eth_contract, self.eth_concise = w3_eth.init_contract('StrideEthContract') 
        self.rsk_contract, self.rsk_concise = w3_eth.init_contract('StrideRSKContract') 
        self.eth_tx = {'from' : config.eth.custodian, 'gas' : config.eth.gas, 'gasPrice' : config.eth.gasPrice} # Convenience 
        self.rsk_tx = {'from' : config.rsk.custodian, 'gas' : config.rsk.gas, 'gasPrice' : config.rsk.gasPrice} # Convenience 

    def start(self):
        self.logger.info('Listening to events ..')
        self.event_q.channel.start_consuming()

    def callback(self, ch, method, properties, body):
        body = str(body, 'utf-8') # body type is bytes (for some reason)
        self.logger.info('Received: %s' % body)   
        if body['method'] == 'init_sbtc2ebtc':
            # TODO: Fork a new thread and  process_txn(body) 

    def process_fwd_txn(self, msg): # sbtc->ebtc
        self.collection.insert_one(json.loads(msg))   
        self.logger.info('msg saved in DB')
        
        # Deposit EBTC to Eth contract
        txn_id = msg['id']
        pwd_hash = msg['pwd_hash']
        user_eth = msg['params']['user'] 
        ebtc_amount = msg['params']['amount']
        timeout_interval = 200 # Arbitrary
        tx_hash = self.eth_concise.fwd_deposit(txn_id, user_eth, pwd_hash,
                      timeout_interval, ebtc_amount, transact = self.eth_tx) 
        self.w3_eth.wait_to_be_mined(tx_hash)

    

def main():
    app = App('/tmp/stride.log', 'custodian-q')
    app.start()

if __name__== '__main__':
    main()
