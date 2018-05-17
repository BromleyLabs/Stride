# This daemon will run by customer at his premises or in his control. 

from utils import *
import json
from pymongo import MongoClient
import datetime

class App:
    def __init__(self, log_file, q_name):
        self.event_q = RabbitMQ(q_name)
        self.event_q.channel.basic_consume(self.callback, queue=q_name,
                                           no_ack=True)
        self.logger = init_logger('CUST',  log_file)
        self.db_client = MongoClient() # Default location 
        self.db = self.db_client['custodian-db']
        self.collection = self.db['transactions'] 

    def start(self):
        self.logger.info('Listening to events ..')
        self.event_q.channel.start_consuming()

    def callback(self, ch, method, properties, body):
        body = str(body, 'utf-8') # body type is bytes (for some reason)
        self.logger.info('Received: %s' % body)   
        self.process(body)

    def process(self, msg):
        self.logger.info('Processed: %s' % msg)   
        #self.collection.insert_one(js)   
        #self.logger.info('msg saved in DB')

def main():
    app = App('/tmp/stride.log', 'custodian-q')
    app.start()

if __name__== '__main__':
    main()
