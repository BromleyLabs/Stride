from web3.auto import w3
from hexbytes import HexBytes
from web3.contract import ConciseContract
import os
from utils import *

CONTRACT_FILE = '../contracts/rsk_deposit_contract.sol'
CONTRACT_NAME = 'RSKDepositContract'
ABI_FILE = os.path.join('../contracts/target/', CONTRACT_NAME + '.abi')
BIN_FILE = os.path.join('../contracts/target/', CONTRACT_NAME + '.bin')
OWNER = w3.eth.accounts[0]
GAS = 4000000 
GAS_PRICE = 10000000000

# This class to be used once contract is deployed
class RSKDepositContract:
    def __init__(self, addr, abi_file):
        self.addr = checksum(addr)
        self.abi_file = abi_file
        abi = open(abi_file, 'rt').read()
        self.contract = w3.eth.contract(abi = abi, address = self.addr)
        self.concise = ConciseContract(self.contract)

    def kill(self):
        
        tx_hash = self.contract.functions.kill().transact({'from' : OWNER, 
                                           'gas' : GAS, 'gasPrice' : GAS_PRICE})
        print('Tx hash: %s' % HexBytes(tx_hash).hex())
    
        tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
        print (tx_receipt) 

    def add_custodian(self, custodian_addr, owner_addr):
        custodian_addr = checksum(custodian_addr)
        owner_addr = checksum(owner_addr)
        tx_hash = self.concise.add_custodian(custodian_addr, 
                                    transact = {'from' : owner_addr,
                                    'gas' : GAS, 'gasPrice' : GAS_PRICE}) 
        print('Tx hash: %s' % HexBytes(tx_hash).hex())
        tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
        print (tx_receipt) 

    def submit_ack(self, txn_id, ack_msg, account_addr):
        # ack_msg is bytearray of 32 bytes, assumed for now
        h_hash, v_int, r, s = sign_bytearray(ack_msg, account_addr)
        tx_hash = self.contract.functions.submit_ack(txn_id, ack_msg, h_hash, v_int, r, s).transact({'from' : account_addr, 'gas' : GAS, 'gasPrice' : GAS_PRICE}) 
                                         
        print('Tx hash: %s' % HexBytes(tx_hash).hex())
        tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
        print (tx_receipt) 

def main():
    rsk = RSKDepositContract('0x73067Ea0C3B4E23f3D73B7022c07C1FF4a7ca069',
                              ABI_FILE)
    ack_msg = bytes(32)
    rsk.submit_ack(0, ack_msg, w3.eth.accounts[2])

if __name__== '__main__':
    main()
