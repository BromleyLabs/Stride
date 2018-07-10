import os

custodian_portal = 'http://localhost:5000/stride/'
eth_ebtc_ratio = 15.0
eth_proof_contract_addr = '0xd78b21a137Be68fBB5E14cCdbb9b2788d88F4666'

class ChainConfig:
    def __init__(self, name):
        self.name = name
        self.gas = None
        self.gas_price = None
        self.token_addr = None
        self.contract_name = None 
        self.contract_path = None
        self.token_contract_name = None # Only for EBTC
        self.abi_file = None
        self.bin_file = None
        self.contract_addr = None 
        self.contract_owner = None
        self.rpc_addr = None
        self.user = None
        self.custodian = None
        self.dest_addr = None  # Destnation address if applicable

rsk = ChainConfig('RSKTestnet')
rsk.contract_addr = '0x971C4b156c05F9978726d703d2b5cD13767D89Fb'
rsk.contract_name = 'StrideRSKContract'
rsk.contract_path = '/home/puneet/crypto/stride/contracts/target'
rsk.gas = 2500000
rsk.gas_price = 1 
rsk.token_addr = '' # NA. SBTC is currency, not token 
rsk.contract_owner = '0x36E7CDF091cbFA3a86611017e813432D98dFD969'
rsk.rpc_addr = 'http://localhost:4444'
#rsk.rpc_addr = 'http://stride.ddns.net:4444'
rsk.user = '0x9d465C631F1D8E47B6113Ab204a9410183fcCE05'
#rsk.user = '0x9d465c631f1d8e47b6113ab204a9410183fcce05' # Lower case
rsk.custodian = '0x2cEb031df9c7e5AF8D4bfd08eFEA7E76fE32F055'
#rsk.custodian = '0x2ceb031df9c7e5af8d4bfd08efea7e76fe32f055' # Lower case
rsk.dest_addr = '0x8518266aCAe14073776De8371153A3389265d955'
rsk.contract_owner = '0x36E7CDF091cbFA3a86611017e813432D98dFD969' 

eth = ChainConfig('ETHRopsten')
eth.contract_addr = '0xD1CE1394173eF6601a4BB4634AF6702473A45749'
eth.contract_name = 'StrideEthContract'
eth.contract_path = '/home/puneet/crypto/stride/contracts/target'
eth.token_contract_name = 'EBTCToken'
eth.gas = 4000000
eth.gas_price = 2500000000 
eth.rpc_addr = 'http://localhost:8545'
#eth.rpc_addr = 'http://stride.ddns.net:8545'
eth.user = '0x9d465C631F1D8E47B6113Ab204a9410183fcCE05'
eth.custodian = '0xadEd5F0Cfd12122F98c450a94a382f0BA7CA65eD'
eth.contract_owner = '0x9d465C631F1D8E47B6113Ab204a9410183fcCE05' 
eth.dest_addr = '' # NA. EBTC is issued to User's Eth address as part of Swap
eth.token_addr = '0xE6cE9BA4F6F112202aCC359887E20466fC31Ab3F' # EBTC


