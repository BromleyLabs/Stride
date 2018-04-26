from web3.auto import w3
import sys 
from hexbytes import HexBytes

GAS = 400000 
GAS_PRICE = 5000000000
OWNER = w3.eth.accounts[0]

def checksum(addr):
    if not w3.isChecksumAddress(addr):
        return w3.toChecksumAddress(addr)
    else:
        return addr

def kill(contract_addr, abi_file, bin_file):
    abi = open(abi_file, 'rt').read()
    bytecode = open(bin_file, 'rt').read()
    contract_addr = checksum(contract_addr)

    contract = w3.eth.contract(abi = abi, address = contract_addr) 
    
    tx_hash = contract.functions.kill().transact({'from' : OWNER, 'gas' : GAS,
                                                  'gasPrice' : GAS_PRICE})
    print('Tx hash: %s' % HexBytes(tx_hash))

    tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
    print ('Tx receipt: %s' % HexBytes(tx_receipt))

def main():
    if len(sys.argv) != 4:
        print ('Usage: python kill.py <contract addr> <abi file> <bin file>')

    kill(sys.argv[1], sys.argv[2], sys.argv[3]) 

if __name__== '__main__':
    main()
