from web3.auto import w3
from hexbytes import HexBytes
from solc import compile_source
from web3.contract import ConciseContract
import os
from utils import *

CONTRACT_FILE = '../contracts/rsk_deposit_contract.sol'
CONTRACT_NAME = 'RSKDepositContract'
ABI_FILE = os.path.join('../contracts/target/', CONTRACT_NAME + '.abi')
BIN_FILE = os.path.join('../contracts/target/', CONTRACT_NAME + '.bin')
OWNER = w3.eth.accounts[0]
GAS = 4000000 
GAS_PRICE = 5000000000

# This class to be used once contract is deployed
class RSKDepositContract:
    def __init__(self, addr, abi_file):
        self.addr = addr
        self.abi_file = abi_file
        abi = open(abi_file, 'rt').read()
        addr = checksum(addr)
        self.contract = w3.eth.contract(abi = abi, address = addr)
        self.concise = ConciseContract(self.contract)

    def kill(self, contract_addr, abi_file, bin_file):
        
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

# This a separate function to be called only once.
def deploy(contract_file, contract_name):
    
    compiled_sol = compile_source(open(contract_file, 'rt').read())
    interface = compiled_sol['<stdin>:' + contract_name] 
       
    contract = w3.eth.contract(abi = interface['abi'], 
                               bytecode = interface['bin'])
    
    tx_hash = contract.deploy(transaction = {'from' : OWNER, 'gas' : GAS, 
                                             'gasPrice' : GAS_PRICE}) 
    print('Tx hash: %s' % HexBytes(tx_hash).hex())

    tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
    print(tx_receipt)


def main():
    contract = RSKDepositContract('0x73067Ea0C3B4E23f3D73B7022c07C1FF4a7ca069',
                                  ABI_FILE)

    contract.add_custodian(w3.eth.accounts[2], w3.eth.accounts[0])

if __name__== '__main__':
    main()
