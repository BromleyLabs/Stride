from web3.auto import w3
from hexbytes import HexBytes
import os
import pika
import uuid
from config import *
import utils
from utils import *
from contracts import *
import json

logger = None

def main():
    global logger
    logger = init_logger('USER')
    utils.logger = logger
    send_q = RabbitMQ('user->custodian')
    send_q.purge()
    receive_q = RabbitMQ('custodian->user')
    receive_q.purge()
    rsk = UserRSKContract(USER_CONTRACT_ADDR, USER_ABI_FILE)

    # Initial transaction 
    logger.info('Initiate txn')
    u =  uuid.uuid4()  # Random 128 bits 
    txn_id = u.int 
    logger.info('Txn Id: 0x%s' % u.hex)
    sbtc_amount = int(0.001 * 1e18) 
    txn_init = json.dumps({'type' : 'INIT', 'txn_id' : txn_id, 
                           'sbtc_amount' : sbtc_amount}) 
    send_q.send(txn_init) 

    # Expect custodian password hash 
    js = expect_msg(receive_q, 'PWD_HASH', txn_id)
    pwd_hash = js['pwd_hash']
    logger.info('Password hash: %s' % pwd_hash) 

    # Init contract
     
    pwd_hash = HexBytes(pwd_hash) 
    tx_hash = rsk.create_transaction(txn_id, USER_RSK, CUSTODIAN_RSK, pwd_hash,
                                     200, sbtc_amount)
    wait_to_be_mined(tx_hash)
    
    # TODO: Next watch for CustodianTransactionCreated event.
    # Check the if the transaction contents are ok 
    # User watches CustodianTransferred() event on Eth

    #print('Approving ..')
    #tx_receipt = erc20_approve(WETH_ADDR, USER_RSK, USER_CONTRACT_ADDR, 
    #                           int(10.0 * 1e18), GAS, GAS_PRICE)

    #print('Transferring..')
    #tx_receipt = rsk.transfer_to_contract(txn_id, USER) 
    
    # TODO: Watch for CustodianExecutionSuccess event and read the password  

    #eth = CustodianEthContract(CUSTODIAN_CONTRACT_ADDR, CUSTODIAN_ABI_FILE)
    #eth.execute(USER_ETH, txn_id, pwd_str)
   
if __name__== '__main__':
    main()
