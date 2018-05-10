from web3.auto import w3
from hexbytes import HexBytes
from solc import compile_source
import os
import sys
from utils import *
from common import *


# This a separate function to be called only once.
def deploy(contract_name):
    #compiled_sol = compile_source(open(contract_file, 'rt').read())
    #interface = compiled_sol['<stdin>:' + contract_name] 
    abi_file = contract_name + '.abi'
    bin_file = contract_name + '.bin'
    contract = w3.eth.contract(abi = open(abi_file, 'rt').read(),
                               bytecode = '0x' + open(bin_file, 'rt').read()) 
    
    tx_hash = contract.deploy(transaction = {'from' : OWNER, 'gas' : GAS, 
                                             'gasPrice' : GAS_PRICE}) 
    wait_to_be_mined(tx_hash)
    

def main():
    if len(sys.argv) != 2:
        print('Usage: python deploy.py <contract name>')
        exit(0)
    deploy(sys.argv[1])

if __name__== '__main__':
    main()
