from web3.auto import w3
from hexbytes import HexBytes

def checksum(addr):
    if not w3.isChecksumAddress(addr):
        return w3.toChecksumAddress(addr)
    else:
        return addr
