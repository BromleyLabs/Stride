# Test script to test response from Custodian portal.
#
# Author: Bon Filey (bonfiley@gmail.com)
# Copyright 2018 Bromley Labs Inc.

import json
import requests

ETH_TXN = '0x30ed16405e1c15c037504458d235122e5153db36bb5c3923f726720436ba8a3a'
RSK_TXN = '0x007b1ba4ee65b1a3d46fbeb4249ef7256f9c0efc25e2fbcf44c421b2fffc11ec'
TXN = ETH_TXN
ETH_PORTAL = 'https://stride.ddns.net/stride/ethereum/ropsten'
RSK_PORTAL = 'https://stride.ddns.net/stride/rsk/testnet'
PORTAL = ETH_PORTAL

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


