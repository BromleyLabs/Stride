from common.utils import *
from common import config
from hexbytes import HexBytes
import rlp
from web3.auto import w3
from trie import Trie 
import trie.utils.nibbles as nibbles

def int_to_buf(a):
     return HexBytes('%s' % hex(a))

def encode_logs(logs):
    encoded_logs = []
    for log in logs:
        address = HexBytes(log['address'])
        topics = log['topics']
        data = HexBytes(log['data'])
        encoded_logs.append([address, topics, data])
    return encoded_logs

def get_rlp_receipt(r): # Receipt
    if r.status == 0: # Ref Ethereum implementation: core/types/receipt.go
        status = b''
    else:
        status = int_to_buf(r.status)  # b'\x01'

    raw_receipt = rlp.encode([status, 
                              int_to_buf(r.cumulativeGasUsed),
                              r.logsBloom, 
                              encode_logs(r.logs)])
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
        if i == receipt.transactionIndex:
            rlp_txn_receipt = value  # We are interested in this txn 
 
    txn_path = rlp.encode(receipt.transactionIndex)
    parent_nodes = []
    t = receipt_trie
    parent_nodes.append(t.root_node)
    node = t.root_node
    nibs = nibbles.bytes_to_nibbles(txn_path)
    for nib in nibs: 
        next_node = rlp.decode(t.db[node[nib]])    
        parent_nodes.append(next_node)
        node = next_node

    rlp_parent_nodes = rlp.encode(parent_nodes)
    print('Calculated hash = %s' % HexBytes(w3.sha3(rlp.encode(t.root_node))).hex())
    print('Receipts root = %s' % HexBytes(block.receiptsRoot).hex()) 

    return rlp_txn_receipt, receipt.blockHash, txn_path, rlp_parent_nodes


if __name__== '__main__':
    from web3.auto import w3    
   
    receipts_trie = Trie(db = {})
    txn_hash = '0x3606ff2b53d5bbd22f6c35473aff06bbde770ed4ce5c9c6f969736206c06b94b'
    r, h, p, nodes = build_receipt_proof(w3, receipts_trie, txn_hash) 

        
        
