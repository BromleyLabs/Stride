from common.utils import *
from common import config
from hexbytes import HexBytes
import rlp
from web3.auto import w3
from trie import HexaryTrie

def int_to_buf(a):
     return HexBytes('%s' % hex(a))

def encode_logs(logs):
    logs = []
    for log in logs:
        address = HexBytes(log['address'])
        topics = log['topics']
        data = HexBytes(log['data'])
        logs.push([address, topics, data])
    return logs

def get_rlp_receipt(r): # Receipt
    status = int_to_buf(r['status']) 
    cummulative_gas = int_to_buf(r['cumulativeGasUsed'])
    bloom_filter = r['logsBloom'] 
    logs = encode_logs(r['logs']) 
    raw_receipt = rlp.encode([status, cummulative_gas, bloom_filter, logs])
    return raw_receipt

def print_node(node):
    for x in node:
        print(HexBytes(x).hex())

def build_receipt_proof(w3, receipt_trie, txn_hash):
    receipt = w3.eth.getTransactionReceipt(txn_hash)
    block = w3.eth.getBlock(receipt.blockHash)
    for i, tr in enumerate(block.transactions):
        path = rlp.encode(i)    
        sibling_receipt = w3.eth.getTransactionReceipt(tr.hex())
        value =  get_rlp_receipt(sibling_receipt) 
        receipt_trie.set(path, value)
 
    print('Original receipts Root = %s' % (block.hash).hex()) 
    print('Root hash = %s' % HexBytes(receipt_trie.root_hash).hex()) 
    root_node = receipt_trie.get_node(receipt_trie.root_hash)
    print_node(receipt_trie.get_node(root_node[0]))

if __name__== '__main__':
    from web3.auto import w3    
   
    receipts_trie = HexaryTrie(db = {})
    txn_hash = '0x3606ff2b53d5bbd22f6c35473aff06bbde770ed4ce5c9c6f969736206c06b94b'
    build_receipt_proof(w3, receipts_trie, txn_hash) 

