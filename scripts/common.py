from web3.auto import w3
from hexbytes import HexBytes
from web3.contract import ConciseContract
import os
from utils import *

USER_CONTRACT_ADDR = '0x8CdfF931a02EBeFeAf07f3b796CF705352bBd3be'
USER_CONTRACT_FILE = '../contracts/user_rsk.sol'
USER_CONTRACT_NAME = 'UserRSKContract'
USER_ABI_FILE = os.path.join('../contracts/target/', USER_CONTRACT_NAME + '.abi')
USER_BIN_FILE = os.path.join('../contracts/target/', USER_CONTRACT_NAME + '.bin')

CUSTODIAN_CONTRACT_ADDR = '0xc778417E063141139Fce010982780140Aa0cD5Ab' 
CUSTODIAN_CONTRACT_FILE = '../contracts/custodian_rsk.sol'
CUSTODIAN_CONTRACT_NAME = 'CustodianEthContract'
CUSTODIAN_ABI_FILE = os.path.join('../contracts/target/', CUSTODIAN_CONTRACT_NAME + '.abi')
CUSTODIAN_BIN_FILE = os.path.join('../contracts/target/', CUSTODIAN_CONTRACT_NAME + '.bin')

GAS = 4000000 
GAS_PRICE = 16000000000
OWNER = w3.eth.accounts[0]
USER = w3.eth.accounts[0]
CUSTODIAN = w3.eth.accounts[2]
ETH_ADDR = w3.eth.accounts[1]
WETH_ADDR = '0xc778417E063141139Fce010982780140Aa0cD5Ab' 

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
        tx_hash = self.concise.execute(txn_id, transact = {'from' : from_addr, 
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
        return tx_hash

    def transfer_to_contract(self, txn_id, from_addr):
        tx_hash = self.concise.transfer_to_contract(txn_id,
                                         transact = {'from' : from_addr, 
                                         'gas' : GAS, 'gasPrice' : GAS_PRICE}) 
        return wait_to_be_mined(tx_hash)

    def execute(self, from_addr, txn_id, pwd_str):
        tx_hash = self.concise.execute(txn_id, transact = {'from' : from_addr, 
                                       'gas' : GAS, 'gasPrice' : GAS_PRICE}) 
        return wait_to_be_mined(tx_hash)

