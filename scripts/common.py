from web3.auto import w3
import os

CONTRACT_ADDR = '0x486E800B7aBbb02De65cC670A44162f69bbA5418' 
CONTRACT_FILE = '../contracts/rsk_deposit_contract.sol'
CONTRACT_NAME = 'RSKDepositContract'
CONTRACT_FILE = '../contracts/rsk_deposit_contract.sol'
CONTRACT_NAME = 'RSKDepositContract'
ABI_FILE = os.path.join('../contracts/target/', CONTRACT_NAME + '.abi')
BIN_FILE = os.path.join('../contracts/target/', CONTRACT_NAME + '.bin')
GAS = 4000000 
GAS_PRICE = 10000000000
OWNER = w3.eth.accounts[0]
USER = w3.eth.accounts[0]
CUSTODIAN = w3.eth.accounts[2]
ETH_ADDR = w3.eth.accounts[1]
WETH_ADDR = '0xc778417E063141139Fce010982780140Aa0cD5Ab' 
