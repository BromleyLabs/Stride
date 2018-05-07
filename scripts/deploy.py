from web3.auto import w3
from hexbytes import HexBytes
from solc import compile_source
import os
from utils import *

CONTRACT_FILE = '../contracts/rsk_deposit_contract.sol'
CONTRACT_NAME = 'RSKDepositContract'
OWNER = w3.eth.accounts[0]
GAS = 4000000 
GAS_PRICE = 10000000000

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
    print('')
    print('Waiting for transaction to get mined ..')
    wait_to_be_mined(txn_hash)
    

def main():
    deploy(CONTRACT_FILE, CONTRACT_NAME)

if __name__== '__main__':
    main()
