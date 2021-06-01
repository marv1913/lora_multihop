import logging

from ipc.java_ipc import JavaIPC
from tests.integration_tests.local_consumer_producer_single_node import LocalConsumerProducer
from util import variables

if __name__ == '__main__':
    variables.MAX_SLEEP_TIME = 0.2
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    module_address = '0200'
    host = None

    read_write = LocalConsumerProducer(host=host, port=5000, module_address=module_address)
    is_server = True

    read_write.start_send_receive_threads(is_server=is_server)
    java_ipc = JavaIPC(ipc_port=6000, message_port=6100, module_address=module_address)
    java_ipc.start_ipc()
    while True:
        if input() == 'exit':
            java_ipc.stop_ipc_instance()
            read_write.stop_local_consumer_producer()
            break
