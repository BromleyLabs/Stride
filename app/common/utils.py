from hexbytes import HexBytes
from web3 import Web3
from web3.contract import ConciseContract
import time
import string
import pika
import logging 
import json
import random
import os
from common import config

def init_logger(module_name, file_name):
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(file_name)
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s]: %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

class RabbitMQ: 
    def __init__(self, qname):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.qname = qname
        self.channel.queue_declare(queue = self.qname) 

    def send(self, msg):
        self.channel.basic_publish(exchange = '', routing_key = self.qname, 
                      body = msg)

    def read(self, blocking = True, timeout = 10 * 60):
        # timeout = -1 means infinite wait
        if timeout < 0:
            timeout = 1e8  # Very high value

        method, header, body = self.channel.basic_get(queue = self.qname, 
                                                   no_ack=True)
        if not blocking:
            return body
        t = 0
        body = None
        while 1: 
            method, header, body = self.channel.basic_get(queue = self.qname, 
                                                     no_ack=True)
            if body is not None or t > timeout:
                break
            time.sleep(1) 
            t += 1

        return body

    def purge(self):
        self.channel.queue_purge(queue = self.qname)
         
    def close(self):
        self.connection.close()


class W3Utils:
    def __init__(self, chain_config, logger):
        self.logger = logger
        self.w3 = Web3(Web3.HTTPProvider(chain_config.rpc_addr))
        self.chain = chain_config
        if chain_config == config.rsk: 
            self.unlock_accounts([self.chain.contract_owner, self.chain.user,
                                  self.chain.custodian], "puneet")
        # Parity accounts assumed to be unlocked while running the node
     
    def init_contract(self, contract_name, contract_addr):
        abi_file = os.path.join(self.chain.contract_path, 
                                contract_name + '.abi')
        abi = open(abi_file, 'rt').read()
        contract = self.w3.eth.contract(abi = abi, 
                                        address = contract_addr) 
        concise = ConciseContract(contract)
        return contract, concise

    def checksum(self, addr):
        if not self.w3.isChecksumAddress(addr):
            return self.w3.toChecksumAddress(addr)
        else:
            return addr

    def generate_random_string(self, length): # Generates random letter string 
        s = ''.join([random.choice(string.ascii_uppercase) for n in range(length)])
        h_hash = self.w3.sha3(text = s) 
        return s, h_hash

    def sign_bytearray(self, barray, account_adr):
        # Returns hex strings like '0x3532..'
        h = HexBytes(barray)
        h_hash = self.w3.sha3(hexstr = h.hex())
        sig = self.w3.eth.sign(account_adr, h_hash) # sig is HexBytes   
        r = self.w3.toBytes(hexstr = HexBytes(sig[0 : 32]).hex())
        s = self.w3.toBytes(hexstr = HexBytes(sig[32 : 64]).hex())
        v = sig[64 : 65]
        v_int = int.from_bytes(v, byteorder='big')
        h_hash = self.w3.toBytes(hexstr = h_hash.hex())
        return h_hash, v_int, r, s
 
    # Functon returns (receipt, status)
    def get_transaction_receipt(self, txn_hash):
        txn_receipt = self.w3.eth.getTransactionReceipt(txn_hash)
        status = 'wait' 
        hash_str = HexBytes(txn_hash).hex()
        if txn_receipt is not None: 
            if txn_receipt['status'] != 1:
                status = 'error' 
                self.logger.error('Transaction: %s' % hash_str)
            if txn_receipt['blockNumber'] is not None:
                self.logger.info('Transaction mined: %s' % hash_str) 
                status = 'mined' 
        return txn_receipt, status

    def wait_to_be_mined(self, txn_hash):
        # timeout in nblocks
        self.logger.info('Tx hash: %s' % HexBytes(txn_hash).hex())
        self.logger.info('Waiting for transaction to get mined')
        while 1: 
            txn_receipt, status = self.get_transaction_receipt(txn_hash)  
            if status == 'error' or status == 'mined': 
                break
            time.sleep(5) 
        self.logger.debug(txn_receipt)
        return status

    def wait_to_be_mined_batch(self, txn_hashes):
        # txn_hashes: list of txn_hash
        # timeout in nblocks
        self.logger.info('Tx hashes: %s' % txn_hashes) 
        self.logger.info('Waiting for transactions to get mined')
        handled = [] 
        while len(handled) != len(txn_hashes): 
            time.sleep(5)
            for i, txn_hash in enumerate(txn_hashes):
                if txn_hash in handled: 
                    continue
                txn_receipt, status = self.get_transaction_receipt(txn_hash)  
                if status == 'error' or status == 'mined':
                    handled.append(txn_hash)
        self.logger.info('All transactions handled')
    
    def erc20_approve(self, erc20_address, from_addr, to_addr, amount, 
                      gas, gas_price):
        erc20_abi = open('erc20.abi', 'rt').read() 
        erc20 = self.w3.eth.contract(abi = erc20_abi, address = erc20_address) 
        concise = ConciseContract(erc20)
        txn_hash = concise.approve(to_addr, amount,
                                transact = {'from': from_addr, 'gas': gas, 
                                            'gasPrice': gas_price}) 
        return self.wait_to_be_mined(txn_hash)

    def event_match(self, event, txn_hash = None, args = None):
        if txn_hash:
            if event['transactionHash'] != txn_hash:
                return False
        if args is not None:
            for k in args:
                if k not in event['args']:
                    return False
                if args[k] != event['args'][k]:
                    return False
        return True

    # expected_args is dict of key value pairs of the event
    def wait_for_event(self, event_filter, txn_hash = None, args = None, 
                       timeout = 200):
        # timout in nblocks
        start = self.w3.eth.blockNumber
        while self.w3.eth.blockNumber < start + timeout: 
            time.sleep(3)
            events = event_filter.get_new_entries()
            if len(events) == 0:
                continue 
            for event in events:
                if self.event_match(event, txn_hash, args):
                    return event                    
 
        self.logger.error('Event wait timeout!') 
        return None

    def unlock_accounts(self, accounts_list, pwd):
        for a in accounts_list:
            self.w3.personal.unlockAccount(a, pwd) 

    def deploy(self, contract_name):
        conf = self.chain
        self.logger.info('Deploying contract %s on %s' % (contract_name, conf.name)) 
        abi_file = os.path.join(conf.contract_path, contract_name + '.abi')
        bin_file = os.path.join(conf.contract_path, contract_name + '.bin')
        abi = open(abi_file, 'rt').read()
        bytecode = '0x' + open(bin_file, 'rt').read() 
        contract = self.w3.eth.contract(abi = abi, bytecode = bytecode)
        txn_hash = contract.constructor().transact({'from' : conf.contract_owner, 
                                         'gas' : conf.gas, 
                                         'gasPrice' : conf.gas_price}) 
        return self.wait_to_be_mined(txn_hash)

    def kill(self, contract_name):
        conf = self.chain_config
        self.logger.info('Killing contract %s on %s' % (contract_name, conf.name)) 
        abi_file = os.path.join(conf.contract_path, contract_name + '.abi')
        bin_file = os.path.join(conf.contract_path, contract_name + '.bin')
        abi = open(conf.abi_file, 'rt').read() 
        contract = self.w3.eth.contract(abi = abi, address = conf.contract_addr)
        concise = ConciseContract(contract)
        txn_hash = concise.kill(transact = {'from' : conf.contract_owner, 
                                 'gas' : conf.gas, 'gasPrice' : conf.gas_price}) 
        return self.wait_to_be_mined(txn_hash)

