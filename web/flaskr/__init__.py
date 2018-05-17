import os
import sys
from flask import Flask, request, abort 
import traceback
from utils import *
import json

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

    event_q = RabbitMQ('custodian-q')

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    logger = init_logger('STRIDE', '/tmp/stride.log')
    
    # a simple page that says hello
    @app.route('/stride', methods=['POST'])
    def stride():
        try:
           if not request.json:
               logger.info('Request does not have json')
               abort(400) 
           event_q.send(request.json)
           return ''  # We can retun json string here  
        except:
           exc_type, exc_value, exc_tb = sys.exc_info()
           logger.error(repr(traceback.format_exception(exc_type, exc_value,
                                          exc_tb)))
           abort(400)

    return app

app = create_app()
