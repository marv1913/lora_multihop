import logging
import os

from lora_multihop.java_ipc import JavaIPC
from tests import LocalConsumerProducer
from lora_multihop import variables

if __name__ == '__main__':
    variables.MAX_SLEEP_TIME = 0.2
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    module_address = os.getenv('MODULE_ADDRESS')
    host = os.getenv('HOST')

    read_write = LocalConsumerProducer(host=host, port=int(os.getenv('MODULE_COMMUNICATION_PORT')),
                                       module_address=module_address)
    is_server = False
    if os.getenv('IS_SERVER').lower() == 'true':
        is_server = True

    read_write.start_send_receive_threads(is_server=is_server)
    java_ipc = JavaIPC(ipc_port=int(os.getenv('IPC_PORT')), message_port=int(os.getenv('MESSAGE_PORT')),
                       module_address=module_address)
    java_ipc.start_ipc()
