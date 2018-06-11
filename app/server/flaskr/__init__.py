import os
import sys
from flask import Flask, request, abort, Response 
import traceback
from common.utils import *
from common import config
import json
import datetime
from hexbytes import HexBytes

def binary_response(b):
    resp = Response(b, status=200, mimetype='application/octet-stream')
    resp.headers['Content-Length'] = len(b) 
    return resp

def process_request(js, conf):
    # NOTE: This function needs protections under try/except as we are not
    # doing error checking over here
    
    if js['method'] == 'eth_getTransactionByHash':
        txn_hex = js['params'] 
        txn_hash_bytes = bytes.fromhex(txn_hex[2:]) # params='0x23AB...' 

        r = conf.w3.eth.getTransactionReceipt(txn_hex) 
        if r['status'] != 1: 
            return binary_response(b'') 

        txn_block = r['blockNumber']
        if txn_block is None: 
            return binary_response(b'') 
        txn_index = r['transactionIndex']
      
        txn = conf.w3.eth.getTransactionFromBlock(txn_block, txn_index)

        txn_block_bytes = txn_block.to_bytes(32, 'big')

        curr_block = conf.w3.eth.blockNumber
        curr_block_bytes = curr_block.to_bytes(32, 'big') 
     
        to_addr_bytes = bytes.fromhex(txn['to'][2:])
         
        input_bytes = bytes.fromhex(txn['input'][2:])

        dest_addr_bytes = input_bytes[0:20]
          
        if conf.chain.name == 'ETHRopsten': 
            amount_bytes = input_bytes[20 : 52]
        elif conf.chain.name == 'RSKTestnet':
            amount = txn['value']
            amount_bytes = amount.to_bytes(32, 'big')

        bytes_to_send = curr_block_bytes + txn_block_bytes + to_addr_bytes \
                        + dest_addr_bytes + amount_bytes 
      
        return binary_response(bytes_to_send) 

    return binary_response(b'') 

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    logger = init_logger('STRIDE', '/tmp/stride.log')
    eth = W3Utils(config.eth, logger)
    rsk = W3Utils(config.rsk, logger) 
    default_page = open('/var/www/html/index.html', 'rt').read()
    
    @app.route('/', methods=['GET'])
    def default_response():
        return default_page

    @app.route('/stride/<chain>/<network>', methods=['POST'])
    def get_transaction_by_hash(chain, network):
        try:
           if not request.json:
               logger.info('Request does not have json')
               return binary_response(b'') 

           js = request.json
           logger.info('Received %s' % js)

           if chain == 'rsk':
               chain_config = rsk 
           elif chain == 'ethereum':
               chain_config = eth
           else:
               raise

           return process_request(js, chain_config)
        except:
           exc_type, exc_value, exc_tb = sys.exc_info()
           logger.error(repr(traceback.format_exception(exc_type, exc_value,
                                          exc_tb)))
           return binary_response(b'') 
   
    return app

app = create_app()
