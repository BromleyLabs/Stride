from web3.auto import w3
from hexbytes import HexBytes
from web3.contract import ConciseContract
import os
from utils import *
from common import *
from approve import approve

# This class to be used once contract is deployed
class RSKDepositContract:
    def __init__(self, addr, abi_file):
        self.addr = checksum(addr)
        self.abi_file = abi_file
        abi = open(abi_file, 'rt').read()
        self.contract = w3.eth.contract(abi = abi, address = self.addr)
        self.concise = ConciseContract(self.contract)

    def add_custodian(self, custodian_addr, owner_addr):
        custodian_addr = checksum(custodian_addr)
        owner_addr = checksum(owner_addr)
        tx_hash = self.concise.add_custodian(custodian_addr, 
                                    transact = {'from' : owner_addr,
                                    'gas' : GAS, 'gasPrice' : GAS_PRICE}) 
        return tx_hash

    def set_penalty(self, wei, owner_addr): 
        tx_hash = self.concise.set_penalty(wei, 
                                    transact = {'from' : owner_addr, 
                                    'gas' : GAS, 'gasPrice' : GAS_PRICE}) 
        return tx_hash 

    def deposit_sbtc(self, amount, from_addr, to_addr): 
        tx_hash = self.concise.deposit_sbtc(amount, to_addr, 
                         transact = {'from' : from_addr, 
                                     'gas' : GAS, 'gasPrice' : GAS_PRICE}) 
        return tx_hash                                         

    def submit_ack(self, txn_id, user, ethr_addr, sbtc_amount, 
                   block_number, custodian):
        ack_msg = bytes() # Empty
        ack_msg += txn_id.to_bytes(32, 'big') 
        ack_msg += bytes(HexBytes(user)) # 20 bytes
        ack_msg += bytes(HexBytes(ethr_addr)) # 20 bytes
        ack_msg += sbtc_amount.to_bytes(32, 'big') 
        ack_msg += block_number.to_bytes(32, 'big') 
        ack_msg_hash, v_int, r, s = sign_bytearray(ack_msg, custodian)

        tx_hash = self.concise.submit_ack(ack_msg, ack_msg_hash, v_int, r, s, 
                                         transact = {'from' : custodian, 
                                         'gas' : GAS, 'gasPrice' : GAS_PRICE}) 
        return tx_hash                                         

    def no_ack_challenge(self, txn_id, user_addr):
        tx_hash = self.concise.no_ack_challenge(txn_id,
                           transact = {'from' : user_addr, 
                                       'gas' : GAS, 'gasPrice' : GAS_PRICE}) 
        return tx_hash                                         


def main():
    rsk = RSKDepositContract(CONTRACT_ADDR, ABI_FILE)
    '''
    tx_hash = rsk.add_custodian(CUSTODIAN, OWNER)
    wait_to_be_mined(tx_hash)

    tx_hash = rsk.set_penalty(int(0.0001 * 10**18), w3.eth.accounts[0])
    wait_to_be_mined(tx_hash)

    approve()

    tx_hash = rsk.deposit_sbtc(int(0.001 * 10**18), USER, ETH_ADDR) 
    wait_to_be_mined(tx_hash)

    '''
    #tx_hash = rsk.no_ack_challenge(1, USER)
    
    tx_hash = rsk.submit_ack(1, USER, ETH_ADDR, int(0.001 * 10**18),  
                      w3.eth.blockNumber + 200, CUSTODIAN) 
    wait_to_be_mined(tx_hash)

if __name__== '__main__':
    main()
