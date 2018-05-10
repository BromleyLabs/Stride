from web3.auto import w3
from hexbytes import HexBytes
from web3.contract import ConciseContract
import os
from utils import *
from common import *
import string
import random

def generate_random_pwd():
    s = ''.join([random.choice(string.ascii_uppercase) for n in range(4)])
    h_hash = w3.sha3(text = s) 
    return s, h_hash

def main():
    contract = CustodianEthContract(CUSTODIAN_CONTRACT_ADDR, CUSTODIAN_ABI_FILE)
    pwd_hash =  HexBytes('0x93f0218b357b9256799540fe638f53f9ab92be1e0457d42c7470c3bd3140d393')
    txn_id = 1
    ebtc_amount = int(0.001 * 1e18) 
    #tx_receipt = contract.create_transaction(txn_id, CUSTODIAN, USER, 
    #                                         pwd_hash, 200, ebtc_amount) 
    # TODO: Next watch for UserTransactionCreated event on RSK.
    # TODO: Check the if the transaction contents are ok 

    #print('Approving..')
    #tx_receipt = erc20_approve(WETH_ADDR, CUSTODIAN, CUSTODIAN_CONTRACT_ADDR, 
    #                           int(10.0 * 1e18), GAS, GAS_PRICE)

    #print('Transferring..')
    #tx_receipt = contract.transfer_to_contract(txn_id, CUSTODIAN) 

    # TODO: Custodian watches UserTransferred event on RSK
    
    pwd_str = 'CAMX' 
    rsk = UserRSKContract(USER_CONTRACT_ADDR, USER_ABI_FILE)
    rsk.execute(CUSTODIAN, txn_id, pwd_str)

if __name__== '__main__':
    main()
