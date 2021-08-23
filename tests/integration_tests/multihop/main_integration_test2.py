import logging

from lora_multihop.java_ipc import JavaIPC
from tests.integration_tests.local_consumer_producer import LocalConsumerProducer

if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    module_address = '0200'

    read_write = LocalConsumerProducer(host='localhost', port=5000, module_address=module_address)
    read_write.start_send_receive_threads(is_server=False)
    java_ipc = JavaIPC(ipc_port=6200, message_port=6300, module_address=module_address)
    java_ipc.start_ipc()

    while True:
        if input() == 'exit':
            java_ipc.stop_ipc_instance()
            read_write.stop_local_consumer_producer()
            break
