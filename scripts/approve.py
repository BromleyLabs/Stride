from web3.auto import w3
import json
from web3.contract import ConciseContract
from hexbytes import HexBytes

GAS = 4000000 
GAS_PRICE = 10000000000
USER = w3.eth.accounts[0] 

erc20_abi = open('erc20.abi', 'rt').read() 
erc20_address = '0xc778417E063141139Fce010982780140Aa0cD5Ab' # WETH
erc20 = w3.eth.contract(abi = erc20_abi, address = erc20_address) 
concise = ConciseContract(erc20)
rsk_contract_address = '0x73067Ea0C3B4E23f3D73B7022c07C1FF4a7ca069'
tx_hash = concise.approve(rsk_contract_address, 10 * 10**18,
                        transact = {'from': USER, 'gas': GAS, 
                                    'gasPrice': GAS_PRICE}) 
print('Tx hash: %s' % HexBytes(tx_hash).hex())
tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
print (tx_receipt) 
