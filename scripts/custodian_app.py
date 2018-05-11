from web3.auto import w3
from hexbytes import HexBytes
import os
import utils
from utils import *
from config import *
from contracts import *
import string
import random

logger = None
def generate_random_pwd():
    s = ''.join([random.choice(string.ascii_uppercase) for n in range(4)])
    h_hash = w3.sha3(text = s) 
    return s, h_hash

def main():
    global logger
    logger = init_logger('CUST')
    utils.logger = logger
    send_q = RabbitMQ('custodian->user')
    receive_q = RabbitMQ('user->custodian')
    contract = CustodianEthContract(CUSTODIAN_CONTRACT_ADDR, 
                                     CUSTODIAN_ABI_FILE) 
    # Wait for INIT msg from user
    logger.info('Waiting for INIT msg from user')
    js = expect_msg(receive_q, 'INIT', None) 
    txn_id = js['txn_id']
    token_amount = js['sbtc_amount']   
    logger.info('INIT rececived from user. txn_id = %s, amount = %d' % 
                 (hex(txn_id), token_amount))
  
    pwd_str, pwd_hash = generate_random_pwd() 
    logger.info('pwd = %s, pwd_hash = %s' % (pwd_str, pwd_hash.hex()))    
    
    msg = json.dumps({'type': 'PWD_HASH', 'txn_id' : txn_id, 'pwd_hash' : pwd_hash.hex()})
    send_q.send(msg)

    #tx_receipt = contract.create_transaction(txn_id, CUSTODIAN_ETH, USER_ETH, 
    #                                         pwd_hash, 200, ebtc_amount) 
    # TODO: Next watch for UserTransactionCreated event on RSK.
    # TODO: Check the if the transaction contents are ok 

    #print('Approving..')
    #tx_receipt = erc20_approve(WETH_ADDR, CUSTODIAN_ETH, CUSTODIAN_CONTRACT_ADDR, 
    #                           int(10.0 * 1e18), GAS, GAS_PRICE)

    #print('Transferring..')
    #tx_receipt = contract.transfer_to_contract(txn_id, CUSTODIAN_ETH) 

    # TODO: Custodian watches UserTransferred event on RSK
    
    #rsk = UserRSKContract(USER_CONTRACT_ADDR, USER_ABI_FILE)
    #rsk.execute(CUSTODIAN_RSK, txn_id, pwd_str)

if __name__== '__main__':
    main()
