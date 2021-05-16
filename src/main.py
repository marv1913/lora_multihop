import logging
import time

import serial

from ipc.java_ipc import JavaIPC
from protocol import consumer_producer
from protocol.protocol_lite import ProtocolLite
from util import module_config


def reset_module():
    import RPi.GPIO as GPIO
    import time

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(18, GPIO.OUT)
    GPIO.output(18, GPIO.LOW)
    time.sleep(1)
    GPIO.output(18, GPIO.HIGH)
    GPIO.cleanup()


if __name__ == '__main__':
    # reset_module()
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    ser = serial.serial_for_url('/dev/ttyS0', baudrate=115200, timeout=20)

    # module_config.config_module()
    consumer_producer.start_send_receive_threads(ser)

    time.sleep(1)
    module_config.set_address('0202')
    time.sleep(2)

    java_ipc = JavaIPC(ipc_port=6000, message_port=6100)
    java_ipc.start_tcp_server()

