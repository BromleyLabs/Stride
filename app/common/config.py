import os

Q_NAME = 'CustQ'

class ChainConfig:
    def __init__(self, name):
        self.name = name
        self.gas = None
        self.gas_price = None
        self.token_addr = None
        self.contract_name = None 
        self.contract_path = None
        self.abi_file = None
        self.bin_file = None
        self.contract_addr = None 
        self.contract_owner = None
        self.rpc_addr = None
        self.user = None
        self.custodian = None

rsk = ChainConfig('RSK')
rsk.contract_addr = '0xBA6Ea9e695cCd31b910BEB97728CD68Bf4b0d556'
rsk.contract_name = 'UserRSKContract'
rsk.contract_path = '../contracts/target'
rsk.abi_file = os.path.join(rsk.contract_path, rsk.contract_name + '.abi')
rsk.bin_file = os.path.join(rsk.contract_path, rsk.contract_name + '.bin')
rsk.gas = 2500000
rsk.gas_price = 1
rsk.token_addr = '0xa4E98ec66E91abA653597501e8D1a7126A1932E3' # SBTC 
rsk.contract_owner = '0x36E7CDF091cbFA3a86611017e813432D98dFD969' 
rsk.rpc_addr = 'http://localhost:4444'
rsk.user = '0x36E7CDF091cbFA3a86611017e813432D98dFD969'
rsk.custodian = '0x2cEb031df9c7e5AF8D4bfd08eFEA7E76fE32F055' 

eth = ChainConfig('ETH')
eth.contract_addr = '0xD88dc1003E1aF3D23DBc2e43a753d3B3054F1d41'
eth.contract_name = 'CustodianEthContract'
eth.contract_path = '../contracts/target'
eth.abi_file = os.path.join(eth.contract_path, eth.contract_name + '.abi')
eth.bin_file = os.path.join(eth.contract_path, eth.contract_name + '.bin')
eth.gas = 4000000
eth.gas_price = 25000000000 
eth.token_addr = '0xc778417E063141139Fce010982780140Aa0cD5Ab' # EBTC
eth.contract_owner = '0x25178B671b933b8cF7c25086C3408856c6dfC52C'
eth.rpc_addr = 'http://localhost:8545'
eth.user = '0x25178B671b933b8cF7c25086C3408856c6dfC52C' 
eth.custodian = '0xe7DC201f8a6D758997C0aF79e5f89AEf55911eC2'

