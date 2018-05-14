from hexbytes import HexBytes
import os
import pika
import uuid
import config
from utils import *
from contracts import *
import json

def main():
    logger = init_logger('USER')
    rsk = W3Utils(config.rsk, logger)
    eth = W3Utils(config.eth, logger) 
    logger = rsk.logger # Either one. Both point to same logger 

    send_q = RabbitMQ('user->custodian')
    send_q.purge()
    receive_q = RabbitMQ('custodian->user')
    receive_q.purge()

    rsk_contract = RSKContract(config.rsk, logger)
    eth_contract = EthContract(config.eth, logger)
    
    logger.info('Starting User transaction process ..')
    logger.info('User RSK account balance = %f' % ( 
                       rsk.w3.eth.getBalance(config.rsk.user) / float(1e18)))
    logger.info('User ETH account balance = %f' % (eth.w3.eth.getBalance(config.eth.user) / float(1e18)))

    # Initial transaction 
    logger.info('Initiate txn')
    u =  uuid.uuid4()  # Random 128 bits 
    txn_id = u.int 
    logger.info('Txn Id: 0x%s' % u.hex)
    sbtc_amount = int(0.0001 * 1e18) 
    txn_init = json.dumps({'type' : 'INIT', 'txn_id' : txn_id, 
                           'sbtc_amount' : sbtc_amount}) 
    send_q.send(txn_init) 

    # Expect custodian password hash 
    js = rsk.expect_msg(receive_q, 'PWD_HASH', txn_id)
    pwd_hash = HexBytes(js['pwd_hash'])
    logger.info('Password hash: %s' % pwd_hash.hex()) 

    exit(0)

    # Init contract
    logger.info('Initializing user side contract')
    tx_receipt = rsk.create_transaction(txn_id, USER_RSK, CUSTODIAN_RSK, 
                                        pwd_hash, 200, sbtc_amount)
    logger.info('User contract initialized')

    # Wait for custodian to init Eth contract 
    logger.info('Waiting for custodian to init contract')
    event_filter = eth.contract.events.CustodianTransactionCreated.createFilter(fromBlock = 'latest')
    wait_for_event(event_filter, txn_id)
    logger.info('CustodianTransactionCreated event received')

    # TODO: Check the if the transaction contents are ok 

    # User watches CustodianTransferred() event on Eth
    logger.info('Waiting for CustodianTransferred event')
    event_filter = eth.contract.events.CustodianTransferred.createFilter(fromBlock = 'latest')
    wait_for_event(event_filter, txn_id)
    logger.info('Custodian Transferred event received')

    logger.info('Approving user to move funds..')
    tx_receipt = erc20_approve(WETH_ADDR, USER_RSK, USER_CONTRACT_ADDR, 
                               int(10.0 * 1e18), GAS, GAS_PRICE)
    logger.info('Approved')

    logger.info('Transferring funds from user to contract')
    tx_receipt = rsk.transfer_to_contract(txn_id, USER_RSK) 
    logger.info('Transferred')
    
    logger.info('Waiting for CustodianExcecutionSuccess event')
    event_filter = rsk.contract.events.CustodianExecutionSuccess.createFilter(fromBlock = 'latest')
    event = wait_for_event(event_filter, txn_id)
    logger.info('CustodianExecutionSuccess event received')
    pwd_str = event['args']['pwd_str']
    logger.info('Pwd string = %s' % pwd_str)
   
    # Now execute contract on Eth side
    logger.info('Executing custodian side contract')
    eth = CustodianEthContract(CUSTODIAN_CONTRACT_ADDR, CUSTODIAN_ABI_FILE)
    eth.execute(USER_ETH, txn_id, pwd_str)
    logger.info('Transaction complete')
   
if __name__== '__main__':
    main()
