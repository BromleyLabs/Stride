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
rsk.contract_addr = '0x02e806DB0B1DF24089223AA2e560819bAD50feb0'
rsk.contract_name = 'StrideRSKContract'
rsk.contract_path = '/home/puneet/crypto/stride/contracts/target'
rsk.gas = 2500000
rsk.gas_price = 1
rsk.token_addr = '' # NA. SBTC is currency, not token 
rsk.contract_owner = '0x36E7CDF091cbFA3a86611017e813432D98dFD969'
rsk.rpc_addr = 'http://localhost:4444'
rsk.user = '0x36E7CDF091cbFA3a86611017e813432D98dFD969' # Checksummed
#rsk.user = '0x36e7cdf091cbfa3a86611017e813432d98dfd969' # lower case
rsk.dest_addr = '0x8518266aCAe14073776De8371153A3389265d955'

eth = ChainConfig('ETHRopsten')
eth.contract_addr = '0xA27a5d5A7ec185D337E91ccB5A5615Ae10B40038'
eth.contract_name = 'StrideEthContract'
eth.contract_path = '/home/puneet/crypto/stride/contracts/target'
eth.token_contract_name = 'EBTCToken'
eth.gas = 4000000
eth.gas_price = 25000000000 
eth.token_addr = '0x4d9Bf35908CDa388b34BE67c880F81E53fDaE7a7' # EBTC token address
eth.contract_owner = '0x25178B671b933b8cF7c25086C3408856c6dfC52C'
eth.rpc_addr = 'http://localhost:8545'
eth.user = '0x25178B671b933b8cF7c25086C3408856c6dfC52C' 
eth.dest_addr = '' # NA

