from web3.auto import w3
from hexbytes import HexBytes
from web3.contract import ConciseContract
import os
from utils import *
from common import *
from approve import approve

class UserRSKContract:
    def __init__(self, addr, abi_file):
        self.addr = checksum(addr)
        self.abi_file = abi_file
        abi = open(abi_file, 'rt').read()
        self.contract = w3.eth.contract(abi = abi, address = self.addr)
        self.concise = ConciseContract(self.contract)

    def create_transaction(self, txn_id, user, custodian, pwd_hash, 
                           timeout_interval, sbtc_amount):
        # pwd_hash assumed in HexBytes(32)
        pwd_hash = w3.toBytes(hexstr = pwd_hash.hex())
        tx_hash = self.concise.create_transaction(txn_id, custodian, pwd_hash,
                                         timeout_interval, sbtc_amount, 
                                         transact = {'from' : user,
                                         'gas' : GAS, 'gasPrice' : GAS_PRICE}) 
        return tx_hash

    def transfer_to_contract(self, txn_id, from_addr):
        tx_hash = self.concise.transfer_to_contract(txn_id,
                                         transact = {'from' : from_addr, 
                                         'gas' : GAS, 'gasPrice' : GAS_PRICE}) 
        return wait_to_be_mined(tx_hash)
  
        
def main():

    rsk = UserRSKContract(USER_CONTRACT_ADDR, USER_ABI_FILE)
    pwd_hash =  HexBytes('0x93f0218b357b9256799540fe638f53f9ab92be1e0457d42c7470c3bd3140d393')
    txn_id = 1
    tx_hash = rsk.create_transaction(txn_id, USER, CUSTODIAN, pwd_hash, 200,
                                     int(0.001 * 1e18)) 
    wait_to_be_mined(tx_hash)
     
    # TODO: Next watch for CustodianTransactionCreated event.
    # Check the if the transaction contents are ok 
    # User watches CustodianTransferred() event on Eth

    tx_receipt = erc20_approve(WETH_ADDR, USER, USER_CONTRACT_ADDR, 
                               int(10.0 * 1e18))

    tx_receipt = contract.transfer_to_contract(txn_id, USER) 
    

if __name__== '__main__':
    main()
