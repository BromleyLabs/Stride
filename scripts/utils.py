from web3.auto import w3
from hexbytes import HexBytes
import time

def checksum(addr):
    if not w3.isChecksumAddress(addr):
        return w3.toChecksumAddress(addr)
    else:
        return addr

def sign_bytearray(barray, account_adr):
    # Returns hex strings like '0x3532..'
    h = HexBytes(barray)
    h_hash = w3.sha3(hexstr = h.hex())
    sig = w3.eth.sign(account_adr, h_hash) # sig is HexBytes   
    r = w3.toBytes(hexstr = HexBytes(sig[0 : 32]).hex())
    s = w3.toBytes(hexstr = HexBytes(sig[32 : 64]).hex())
    v = sig[64 : 65]
    v_int = int.from_bytes(v, byteorder='big')
    h_hash = w3.toBytes(hexstr = h_hash.hex())
    return h_hash, v_int, r, s

def wait_to_be_mined(tx_hash):
    print('Tx hash: %s' % HexBytes(tx_hash).hex())
    print('Waiting for transaction to get mined..')
    first = True 
    while 1:
        tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
        if tx_receipt is None:
            time.sleep(10)
            continue

        if first:
            print(tx_receipt)
            first = False 

        if tx_receipt['status'] != 1:
            print('ERROR in transaction')
            break 

        if tx_receipt['blockNumber'] is not None:
            print('Transaction mined')
            break

        time.sleep(10) 

    print('')
    print(tx_receipt)
    return tx_receipt

    
def erc20_approve(erc20_address, from_addr, to_addr, amount):
    erc20_abi = open('erc20.abi', 'rt').read() 
    erc20_address = WETH_ADDR 
    erc20 = w3.eth.contract(abi = erc20_abi, address = erc20_address) 
    concise = ConciseContract(erc20)
    tx_hash = concise.approve(CONTRACT_ADDR, amount,
                            transact = {'from': from_addr, 'gas': GAS, 
                                        'gasPrice': GAS_PRICE}) 
    return wait_to_be_mined(tx_hash)
