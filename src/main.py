import logging
import time

import serial

from lora_multihop import serial_connection, module_config
from lora_multihop.ipc import IPC

if __name__ == '__main__':
    config_str = 'AT+CFG=433500000,20,9,7,1,1,0,0,0,0,3000,8,4'

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    ser = serial.serial_for_url('/dev/ttyS0', baudrate=115200, timeout=20)

    serial_connection.start_send_receive_threads(ser)

    time.sleep(1)
    module_config.config_module(config_str)
    time.sleep(1)
    module_config.set_address('0200')  # set address of LoRa modem
    time.sleep(2)

    ipc = IPC(ipc_port=6000, message_port=6100)  # set ports for both TCP sockets
    ipc.start_ipc()  # start application

