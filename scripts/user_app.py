from web3.auto import w3
from hexbytes import HexBytes
from web3.contract import ConciseContract
import os
from utils import *
from common import *

def main():
    rsk = UserRSKContract(USER_CONTRACT_ADDR, USER_ABI_FILE)
    pwd_hash =  HexBytes('0x93f0218b357b9256799540fe638f53f9ab92be1e0457d42c7470c3bd3140d393')
    txn_id = 1
    #tx_hash = rsk.create_transaction(txn_id, USER_RSK, CUSTODIAN_RSK, pwd_hash, 200,
    #                                 int(0.001 * 1e18)) 
    #wait_to_be_mined(tx_hash)
     
    # TODO: Next watch for CustodianTransactionCreated event.
    # Check the if the transaction contents are ok 
    # User watches CustodianTransferred() event on Eth

    #print('Approving ..')
    #tx_receipt = erc20_approve(WETH_ADDR, USER_RSK, USER_CONTRACT_ADDR, 
    #                           int(10.0 * 1e18), GAS, GAS_PRICE)

    #print('Transferring..')
    #tx_receipt = rsk.transfer_to_contract(txn_id, USER) 
    
    # TODO: Watch for CustodianExecutionSuccess event and read the password  

    pwd_str = 'CAMX' 
    eth = CustodianEthContract(CUSTODIAN_CONTRACT_ADDR, CUSTODIAN_ABI_FILE)
    eth.execute(USER_ETH, txn_id, pwd_str)
   
if __name__== '__main__':
    main()
