from web3.auto import w3
from hexbytes import HexBytes
from web3.contract import ConciseContract
import os
from utils import *
from config import *

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

    def execute(self, from_addr, txn_id, pwd_str):
        tx_hash = self.concise.execute(txn_id, pwd_str, 
                                       transact = {'from' : from_addr, 
                                       'gas' : GAS, 'gasPrice' : GAS_PRICE}) 
        return wait_to_be_mined(tx_hash)

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
        return wait_to_be_mined(tx_hash)

    def transfer_to_contract(self, txn_id, from_addr):
        tx_hash = self.concise.transfer_to_contract(txn_id,
                                         transact = {'from' : from_addr, 
                                         'gas' : GAS, 'gasPrice' : GAS_PRICE}) 
        return wait_to_be_mined(tx_hash)

    def execute(self, from_addr, txn_id, pwd_str):
        tx_hash = self.concise.execute(txn_id, pwd_str, 
                                       transact = {'from' : from_addr, 
                                       'gas' : GAS, 'gasPrice' : GAS_PRICE}) 
        return wait_to_be_mined(tx_hash)

