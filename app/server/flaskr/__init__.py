import os
import sys
from flask import Flask, request, abort 
import traceback
from common.utils import *
from common import config
import json
import datetime

def process_request(js, conf):
    # NOTE: This function needs protections under try/except as we are not
    # doing error checking over here
    
    if js['method'] == 'eth_getTransactionByHash':
        tx_hash_bytes = bytes.fromhex(js['params'][2:]) # params='0x23AB...' 

        curr_block = conf.w3.eth.blockNumber
        curr_block_bytes = curr_block.to_bytes(32, 'big') 
        

     return ''

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
    
    @app.route('stride/<chain>/<network>', methods=['POST'])
    def get_transaction_by_hash(chain, network):
        try:
           if not request.json:
               logger.info('Request does not have json')
               return '' 

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
           return '' 

    return app

app = create_app()
