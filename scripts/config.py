from web3.auto import w3
import os

USER_CONTRACT_ADDR = '0x8CdfF931a02EBeFeAf07f3b796CF705352bBd3be'
USER_CONTRACT_FILE = '../contracts/user_rsk.sol'
USER_CONTRACT_NAME = 'UserRSKContract'
USER_ABI_FILE = os.path.join('../contracts/target/', USER_CONTRACT_NAME + '.abi')
USER_BIN_FILE = os.path.join('../contracts/target/', USER_CONTRACT_NAME + '.bin')

CUSTODIAN_CONTRACT_ADDR = '0x4773c30F30A5aBC063E82e648Ce16a8c11Db32EB'
CUSTODIAN_CONTRACT_FILE = '../contracts/custodian_rsk.sol'
CUSTODIAN_CONTRACT_NAME = 'CustodianEthContract'
CUSTODIAN_ABI_FILE = os.path.join('../contracts/target/', CUSTODIAN_CONTRACT_NAME + '.abi')
CUSTODIAN_BIN_FILE = os.path.join('../contracts/target/', CUSTODIAN_CONTRACT_NAME + '.bin')

GAS = 4000000 
GAS_PRICE = 25000000000
OWNER = w3.eth.accounts[0]
USER_RSK = w3.eth.accounts[0]
USER_ETH = w3.eth.accounts[1]
CUSTODIAN_ETH = w3.eth.accounts[3]
CUSTODIAN_RSK = w3.eth.accounts[2] 

WETH_ADDR = '0xc778417E063141139Fce010982780140Aa0cD5Ab' 

