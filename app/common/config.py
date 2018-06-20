import os

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
        self.dest_addr = None  # Destnation address if applicable

rsk = ChainConfig('RSKTestnet')
rsk.contract_addr = '0x3A252BF53F0f0121cf196D0F7Fe20C2e191F0C69'
rsk.contract_name = 'StrideRSKContract'
rsk.contract_path = '/home/puneet/crypto/stride/contracts/target'
rsk.gas = 2500000
rsk.gas_price = 1 
rsk.token_addr = '' # NA. SBTC is currency, not token 
rsk.contract_owner = '0x36E7CDF091cbFA3a86611017e813432D98dFD969'
rsk.rpc_addr = 'http://localhost:4444'
#rsk.rpc_addr = 'http://stride.ddns.net:4444'
rsk.user = '0x36E7CDF091cbFA3a86611017e813432D98dFD969' # Checksummed
#rsk.user = '0x36e7cdf091cbfa3a86611017e813432d98dfd969' # lower case
rsk.dest_addr = '0x8518266aCAe14073776De8371153A3389265d955'
rsk.contract_owner = '0x36E7CDF091cbFA3a86611017e813432D98dFD969' 

eth = ChainConfig('ETHRopsten')
eth.contract_addr = '0xbBe616c0dA023275B357f6002B655F3B6848b7F5'
eth.contract_name = 'StrideEthContract'
eth.contract_path = '/home/puneet/crypto/stride/contracts/target'
eth.token_contract_name = 'EBTCToken'
eth.gas = 4000000
#eth.gas_price = 25000000000 
eth.gas_price = 2500000000 
eth.rpc_addr = 'http://localhost:8545'
#eth.rpc_addr = 'http://stride.ddns.net:8545'
eth.user = '0x9d465C631F1D8E47B6113Ab204a9410183fcCE05'
eth.contract_owner = '0x9d465C631F1D8E47B6113Ab204a9410183fcCE05' 
eth.dest_addr = '' # NA
eth.token_addr = '0xE6cE9BA4F6F112202aCC359887E20466fC31Ab3F' # EBTC

