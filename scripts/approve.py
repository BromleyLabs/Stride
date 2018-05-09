from web3.auto import w3
import json
from web3.contract import ConciseContract
from hexbytes import HexBytes
from utils import *
from common import *

def approve():
    erc20_abi = open('erc20.abi', 'rt').read() 
    erc20_address = WETH_ADDR 
    erc20 = w3.eth.contract(abi = erc20_abi, address = erc20_address) 
    concise = ConciseContract(erc20)
    tx_hash = concise.approve(CONTRACT_ADDR, 10 * 10**18,
                            transact = {'from': USER, 'gas': GAS, 
                                        'gasPrice': GAS_PRICE}) 
    wait_to_be_mined(tx_hash)
    tx_hash = concise.approve(CONTRACT_ADDR, 10 * 10**18,
                            transact = {'from': CUSTODIAN, 'gas': GAS, 
                                        'gasPrice': GAS_PRICE}) 
    wait_to_be_mined(tx_hash)

if __name__== '__main__':
    approve() 
