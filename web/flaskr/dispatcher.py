from utils import *

logger = None

def callback(ch, method, properties, body):
    logger.info('Received: %s' % body)   

def main():
    global logger
    event_q = RabbitMQ('EventQ')
    logger = init_logger('DISP', '/tmp/stride.log')
    event_q.channel.basic_consume(callback, queue='EventQ', no_ack=True)
                                  
    logger.info('Listening to events on EventQ..')
    event_q.channel.start_consuming()

if __name__== '__main__':
    main()
