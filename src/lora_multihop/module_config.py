import logging

from lora_multihop import serial_connection, variables


def config_module(configuration=variables.MODULE_CONFIG):
    if serial_connection.execute_command(configuration, [variables.STATUS_OK]):
        serial_connection.execute_command('AT+SEND=1', [variables.STATUS_OK])
        serial_connection.execute_command('a', ['AT,SENDING', 'AT,SENDED'])
        logging.debug('module config successfully set')
        return True
    logging.warning("could not set module config")
    return False


def set_address(address):
    cmd = f'AT+ADDR={address}'
    if serial_connection.execute_command(serial_connection.str_to_bytes(cmd), [variables.STATUS_OK]):
        logging.debug(f'module address successfully set to: {address}')
        return True
    logging.warning("could not set module address")
    return False


def get_current_address():
    serial_connection.execute_command(serial_connection.str_to_bytes(variables.GET_ADDR))
    addr = serial_connection.response_q.get(variables.COMMAND_VERIFICATION_TIMEOUT)
    addr = serial_connection.bytes_to_str(addr)
    addr_as_list = addr.split(variables.LORA_MODULE_DELIMITER)
    if addr_as_list[0].strip() != 'AT' or addr_as_list[2].strip() != 'OK':
        raise ValueError('could not get address of module')
    return addr_as_list[1]
