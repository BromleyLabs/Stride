from web3.auto import w3
from web3.contract import ConciseContract
from hexbytes import HexBytes
import sys
import os

CONTRACT_NAME = 'RSKDepositContract'
ABI_FILE = os.path.join('../contracts/target/', CONTRACT_NAME + '.abi')

GAS = 4000000 
GAS_PRICE = 10000000000
OWNER = w3.eth.accounts[0] 

def main():
    if len(sys.argv) != 2:
        print('Usage: python kill.py <contract address>')
        exit(0)
       
    contract_addr = sys.argv[1] 
    abi = open(ABI_FILE, 'rt').read() 
 
    contract = w3.eth.contract(abi = abi, address = contract_addr)
    concise = ConciseContract(contract)
    tx_hash = concise.kill(transact = {'from' : OWNER, 'gas' : 
                                      GAS, 'gasPrice' : GAS_PRICE})
    print('Tx hash: %s' % HexBytes(tx_hash).hex())
 
    tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
    print ('Status = %s' % tx_receipt['status']) 

if __name__== '__main__':
    main()
