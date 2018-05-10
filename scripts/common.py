from web3.auto import w3
import os

USER_CONTRACT_ADDR = ''
USER_CONTRACT_FILE = '../contracts/user_rsk.sol'
USER_CONTRACT_NAME = 'UserRSKContract'
USER_ABI_FILE = os.path.join('../contracts/target/', USER_CONTRACT_NAME + '.abi')
USER_BIN_FILE = os.path.join('../contracts/target/', USER_CONTRACT_NAME + '.bin')

CUSTODIAN_CONTRACT_ADDR = ''
CUSTODIAN_CONTRACT_FILE = '../contracts/custodian_rsk.sol'
CUSTODIAN_CONTRACT_NAME = 'CustodianEthContract'
CUSTODIAN_ABI_FILE = os.path.join('../contracts/target/', CUSTODIAN_CONTRACT_NAME + '.abi')
CUSTODIAN_BIN_FILE = os.path.join('../contracts/target/', CUSTODIAN_CONTRACT_NAME + '.bin')

GAS = 4000000 
GAS_PRICE = 10000000000
OWNER = w3.eth.accounts[0]
USER = w3.eth.accounts[0]
CUSTODIAN = w3.eth.accounts[2]
ETH_ADDR = w3.eth.accounts[1]
WETH_ADDR = '0xc778417E063141139Fce010982780140Aa0cD5Ab' 

