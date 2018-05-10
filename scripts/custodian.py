from web3.auto import w3
from hexbytes import HexBytes
from web3.contract import ConciseContract
import os
from utils import *
from common import *
import string
import random

class CustodianEthContract:
    def __init__(self, addr, abi_file):
        self.addr = checksum(addr)
        self.abi_file = abi_file
        abi = open(abi_file, 'rt').read()
        self.contract = w3.eth.contract(abi = abi, address = self.addr)
        self.concise = ConciseContract(self.contract)

    def create_transaction(self, txn_id, custodian, user, pwd_hash, 
                           timeout_interval, ebtc_amount):
        # pwd_hash assumed in HexBytes(32)
        pwd_hash = w3.toBytes(hexstr = pwd_hash.hex())
        tx_hash = self.concise.create_transaction(txn_id, user, pwd_hash,
                                         timeout_interval, ebtc_amount, 
                                         transact = {'from' : custodian,
                                         'gas' : GAS, 'gasPrice' : GAS_PRICE}) 
        return wait_to_be_mined(tx_hash)

    def transfer_to_contract(self, txn_id, from_addr):
        tx_hash = self.concise.transfer_to_contract(txn_id,
                                         transact = {'from' : from_addr, 
                                         'gas' : GAS, 'gasPrice' : GAS_PRICE}) 
        return wait_to_be_mined(tx_hash)

def generate_random_pwd():
    s = ''.join([random.choice(string.ascii_uppercase) for n in range(4)])
    h_hash = w3.sha3(text = s) 
    return s, h_hash

def main():

    contract = CustodianEthContract(CUSTODIAN_CONTRACT_ADDR, CUSTODIAN_ABI_FILE)
    pwd_hash =  HexBytes('0x93f0218b357b9256799540fe638f53f9ab92be1e0457d42c7470c3bd3140d393')
    txn_id = 1
    ebtc_amount = int(0.001 * 1e18) 
    tx_receipt = contract.create_transaction(txn_id, CUSTODIAN, USER, 
                                             pwd_hash, 200, ebtc_amount) 
    # TODO: Next watch for UserTransactionCreated event on RSK.
    # TODO: Check the if the transaction contents are ok 

    tx_receipt = erc20_approve(WETH_ADDR, CUSTODIAN, CUSTODIAN_CONTRACT_ADDR, 
                               int(10.0 * 1e18))

    tx_receipt = contract.transfer_to_contract(txn_id, CUSTODIAN) 
 
    # TODO: Custodian watches UserTransferred event on RSK


if __name__== '__main__':
    main()
