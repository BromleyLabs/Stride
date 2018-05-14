from web3.auto import w3
from hexbytes import HexBytes
from web3.contract import ConciseContract
import os
from utils import *
import config

class EthContract:
    def __init__(self, config, logger):
        self.config = config
        self.eth = W3Utils(config, logger)
        abi = open(self.config.abi_file, 'rt').read()
        self.contract = self.eth.w3.eth.contract(abi = abi, 
                                        address = self.config.contract_addr) 
        self.concise = ConciseContract(self.contract)

    def create_transaction(self, txn_id, custodian, user, pwd_hash, 
                           timeout_interval, ebtc_amount):
        # pwd_hash assumed in HexBytes(32)
        pwd_hash = self.eth.w3.toBytes(hexstr = pwd_hash.hex())
        tx_hash = self.concise.create_transaction(txn_id, user, pwd_hash,
                                           timeout_interval, ebtc_amount, 
                                           transact = {'from' : user, 
                                           'gas' : self.config.gas, 
                                           'gasPrice' : self.config.gas_price})
        return self.eth.wait_to_be_mined(tx_hash)

    def transfer_to_contract(self, txn_id, from_addr):
        tx_hash = self.concise.transfer_to_contract(txn_id,
                                           transact = {'from' : user, 
                                           'gas' : self.config.gas, 
                                           'gasPrice' : self.config.gas_price})
        return self.eth.wait_to_be_mined(tx_hash)

    def request_refund(self, txn_id, from_addr):
        tx_hash = self.concise.transfer_to_contract(txn_id,
                                         transact = {'from' : from_addr, 
                                         'gas' : self.config.gas, 
                                         'gasPrice' : self.config.gas_price}) 
        return self.eth.wait_to_be_mined(tx_hash)

    def execute(self, from_addr, txn_id, pwd_str):
        tx_hash = self.concise.execute(txn_id, pwd_str, 
                                           transact = {'from' : user, 
                                           'gas' : self.config.gas, 
                                           'gasPrice' : self.config.gas_price})
        return self.eth.wait_to_be_mined(tx_hash)

class RSKContract:
    def __init__(self, config, logger): 
        self.config = config
        self.rsk = W3Utils(config, logger)
        abi = open(self.config.abi_file, 'rt').read()
        self.contract = self.rsk.w3.eth.contract(abi = abi, 
                                         address = self.config.contract_addr) 
        self.concise = ConciseContract(self.contract)

    def create_transaction(self, txn_id, user, custodian, pwd_hash, 
                           timeout_interval, sbtc_amount):
        # pwd_hash assumed in HexBytes(32)
        pwd_hash = self.rsk.w3.toBytes(hexstr = pwd_hash.hex())
        tx_hash = self.concise.create_transaction(txn_id, custodian, pwd_hash,
                                      timeout_interval, sbtc_amount, 
                                      transact = {'from' : user, 
                                        'gas' : self.config.gas, 
                                        'gasPrice' : self.config.gas_price})
        return self.rsk.wait_to_be_mined(tx_hash)

    def transfer_to_contract(self, txn_id, from_addr):
        tx_hash = self.concise.transfer_to_contract(txn_id,
                                         transact = {'from' : from_addr, 
                                         'gas' : self.config.gas, 
                                         'gasPrice' : self.config.gas_price})
        return self.rsk.wait_to_be_mined(tx_hash)

    def request_refund(self, txn_id, from_addr):
        tx_hash = self.concise.transfer_to_contract(txn_id,
                                         transact = {'from' : from_addr, 
                                         'gas' : self.config.gas, 
                                         'gasPrice' : self.config.gas_price}) 
        return self.rsk.wait_to_be_mined(tx_hash)


    def execute(self, from_addr, txn_id, pwd_str):
        tx_hash = self.concise.execute(txn_id, pwd_str, 
                                       transact = {'from' : from_addr, 
                                       'gas' : self.config.gas, 
                                       'gasPrice' : self.config.gas_price}) 
        return self.rsk.wait_to_be_mined(tx_hash)

