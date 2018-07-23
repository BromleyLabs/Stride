# This script is to be run as server for custodian to issue secret password
# to user on request
#
# Author: Bon Filey (bonfiley@gmail.com)
# Copyright 2018 Bromley Labs Inc.

import os
import sys
from flask import Flask, request, abort, Response 
import traceback
from common.utils import *
from common import config
import json
import datetime
from hexbytes import HexBytes

def process_request(js, chain):
    if js['method'] == 'init_sbtc2ebtc':
        pwd_str, pwd_hash = chain.generate_random_string(4)
        js['pwd_str'] = pwd_str
        js['pwd_hash'] = pwd_hash.hex()
        result = pwd_hash.hex()
        return_msg = json.dumps({'jsonrpc' : '2.0', 'result' : result,
                                 'id' : js['id']})
    return js, return_msg  

def create_app():
    app = Flask(__name__)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    logger = init_logger('STRIDE', '/tmp/stride.log')
    eth = W3Utils(config.eth, logger)
    rsk = W3Utils(config.rsk, logger) 
    event_q = RabbitMQ('custodian-q')
    default_page = open('/var/www/html/index.html', 'rt').read()
    
    @app.route('/', methods=['GET'])
    def default_response():
        return default_page

    @app.route('/stride/', methods=['POST'])
    def init_sbtc2ebtc():
        try:
           logger.info(request.headers)
           if not request.is_json:
               logger.info('Request does not have JSON')
               return "Request does not have JSON", 400

           js, msg = process_request(request.json, eth)  
           js['date'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
           event_q.send(json.dumps(js)) 
           return msg
        except:
           exc_type, exc_value, exc_tb = sys.exc_info()
           logger.error(repr(traceback.format_exception(exc_type, exc_value,
                                          exc_tb)))
           abort(400) 
   
    return app

app = create_app()
