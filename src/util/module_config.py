import logging

from protocol import consumer_producer
from util import variables


def config_module(configuration=variables.MODULE_CONFIG):
    configuration = configuration + '\r\n'
    if consumer_producer.execute_command(configuration, [variables.STATUS_OK]):
        logging.debug('module config successfully set')
        return True
    logging.warning("could not set module config")
    return False


def get_current_address():
    consumer_producer.execute_command(variables.GET_ADDR)
    addr = consumer_producer.response_q.get(variables.COMMAND_VERIFICATION_TIMEOUT)
    print(addr)
    addr_as_list = addr.split(variables.LORA_MODULE_DELIMITER)
    if addr_as_list[0].strip() != 'AT' or addr_as_list[2].strip() != 'OK':
        raise ValueError('could not get address of module')
    return addr_as_list[1]
