import logging

from protocol import consumer_producer
from util import variables


class Communicator:

    def __init__(self, protocol_obj):
        variables.MY_ADDRESS = consumer_producer.get_current_address_from_module()
        logging.info('loaded address of module: {}'.format(variables.MY_ADDRESS))
        self.protocol = protocol_obj
        self.protocol.start_protocol_thread()
