from web3 import Web3
from hexbytes import HexBytes
import sys
from utils import *
import utils
import config

def main():
    if len(sys.argv) != 2:
        print('Usage: python kill.py <rsk | eth>')
        exit(0)

    logger = init_logger('KILL', 'stride.log')
    if sys.argv[1] == 'rsk':
        chain = W3Utils(config.rsk, logger)
    elif sys.argv[1] == 'eth':
        chain = W3Utils(config.eth, logger)
    else:
        printf('Incorrect argument')

    chain.kill()

if __name__== '__main__':
    main()
