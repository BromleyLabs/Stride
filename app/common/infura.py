# Sample script to query infura server

import requests
import json
import urllib

js = {
    'jsonrpc' : '2.0', 
    'id' : 23, 
    'method' : 'eth_getTransactionByHash', 
    'params' : ['0x2ddf1f109301f184c0c734d76c194735f84ec60c8f3c0243e58b1a69e1b486d4']
}
r = requests.post('https://ropsten.infura.io/rWjoIVMZaYJbccSEmLQn', json = js)
print(r)
print(r.content)

