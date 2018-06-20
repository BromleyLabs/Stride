import json
import requests

ETH_TXN = '0x9d11a21d0a2ca8a644a62a70c67ae740adc193e31c1e23079b307e0836c93ab4'
RSK_TXN = '0x007b1ba4ee65b1a3d46fbeb4249ef7256f9c0efc25e2fbcf44c421b2fffc11ec'
TXN = RSK_TXN
ETH_PORTAL = 'https://sectechbromley.ddns.net/stride/ethereum/ropsten'
RSK_PORTAL = 'https://sectechbromley.ddns.net/stride/rsk/testnet'
PORTAL = RSK_PORTAL

js = {'jsonrpc' : '2.0', 'id' : 23, 'method' : 'eth_getTransactionByHash', 
      'params' :  TXN}

r = requests.post(PORTAL, json = js, verify=False)
print(r.headers)
print(r.links)
print(r.encoding)
print(r.status_code)
if r.status_code != requests.codes.ok:
    print('Incorrect response code = %d' % r.status_code)
print('Size = %s' % len(r.content))
print('Response = %s' % r.content)


