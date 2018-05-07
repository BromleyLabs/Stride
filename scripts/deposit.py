from web3.auto import w3
from hexbytes import HexBytes
from web3.contract import ConciseContract
import os
from utils import *
from common import *

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
        return tx_hash

    def set_penality(self, wei, owner_addr): 
        tx_hash = self.concise.set_penality(wei, 
                                    transact = {'from' : owner_addr, 
                                    'gas' : GAS, 'gasPrice' : GAS_PRICE}) 
        return tx_hash 

    def deposit_sbtc(self, amount, from_addr, to_addr): 
        tx_hash = self.concise.deposit_sbtc(amount, to_addr, 
                         transact = {'from' : from_addr, 
                                     'gas' : GAS, 'gasPrice' : GAS_PRICE}) 
        return tx_hash                                         

    def submit_ack(self, txn_id, ack_msg, account_addr):
        # ack_msg is bytearray of 32 bytes, assumed for now
        h_hash, v_int, r, s = sign_bytearray(ack_msg, account_addr)
        tx_hash = self.concise.submit_ack(txn_id, ack_msg, h_hash, v_int, r, s).transact({'from' : account_addr, 'gas' : GAS, 'gasPrice' : GAS_PRICE}) 
        return tx_hash                                         

    def no_ack_challenge(self, txn_id, user_addr):
        tx_hash = self.concise.no_ack_challenge(txn_id,
                           transact = {'from' : user_addr, 
                                       'gas' : GAS, 'gasPrice' : GAS_PRICE}) 
        return tx_hash                                         


def main():
    rsk = RSKDepositContract(CONTRACT_ADDR, ABI_FILE)
    #ack_msg = bytes(32)
    #rsk.submit_ack(0, ack_msg, w3.eth.accounts[2])
    #tx_hash = rsk.add_custodian(w3.eth.accounts[2], w3.eth.accounts[0]) 
    #tx_hash = rsk.set_penality(int(0.0001 * 10**18), w3.eth.accounts[0])
    #tx_hash = rsk.deposit_sbtc(int(0.001 * 10**18), USER, ETH_ADDR) 
    tx_hash = rsk.no_ack_challenge(1, USER)
    wait_to_be_mined(tx_hash)

if __name__== '__main__':
    main()
