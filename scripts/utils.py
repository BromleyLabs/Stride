from web3.auto import w3
from hexbytes import HexBytes
from web3.contract import ConciseContract
import time
import pika
import logging 
import json

logger = None

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

def checksum(addr):
    if not w3.isChecksumAddress(addr):
        return w3.toChecksumAddress(addr)
    else:
        return addr

def sign_bytearray(barray, account_adr):
    # Returns hex strings like '0x3532..'
    h = HexBytes(barray)
    h_hash = w3.sha3(hexstr = h.hex())
    sig = w3.eth.sign(account_adr, h_hash) # sig is HexBytes   
    r = w3.toBytes(hexstr = HexBytes(sig[0 : 32]).hex())
    s = w3.toBytes(hexstr = HexBytes(sig[32 : 64]).hex())
    v = sig[64 : 65]
    v_int = int.from_bytes(v, byteorder='big')
    h_hash = w3.toBytes(hexstr = h_hash.hex())
    return h_hash, v_int, r, s

def wait_to_be_mined(tx_hash):
    logger.info('Tx hash: %s' % HexBytes(tx_hash).hex())
    logger.info('Waiting for transaction to get mined')
    while 1:
        tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
        if tx_receipt is None:
            time.sleep(10)
            continue

        if tx_receipt['status'] != 1:
            logger.info('ERROR in transaction')
            break 

        if tx_receipt['blockNumber'] is not None:
            logger.info('Transaction mined')
            break

        time.sleep(10) 

    logger.debug(tx_receipt)
    return tx_receipt

def erc20_approve(erc20_address, from_addr, to_addr, amount, gas, gas_price):
    erc20_abi = open('erc20.abi', 'rt').read() 
    erc20 = w3.eth.contract(abi = erc20_abi, address = erc20_address) 
    concise = ConciseContract(erc20)
    tx_hash = concise.approve(to_addr, amount,
                            transact = {'from': from_addr, 'gas': gas, 
                                        'gasPrice': gas_price}) 
    return wait_to_be_mined(tx_hash)


def init_logger(module_name):
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('log.txt')
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

def expect_msg(q, msg_type, txn_id):
    js = {}
    while 1:
        msg = q.read() 
        if msg is None:
            logger.error('Did not receive msg. Timedout.') 
            break
        msg = msg.decode('utf-8') 
        js = json.loads(msg)
        if txn_id is None:
            if js['type'] == msg_type: 
                break
        else:   
            if js['txn_id'] == txn_id and js['type'] == msg_type: 
                break

    return js

def wait_for_event(event_filter, txn_id):
    found = False
    while not found: 
        events = event_filter.get_new_entries()
        for event in events:
            if event['args']['txn_id'] == txn_id:
                logger.info('Event received')
                logger.debug(event)
                found = True
                break
        time.sleep(3)
    return event
