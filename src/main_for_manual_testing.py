import logging
import time

import serial

from ipc.java_ipc import JavaIPC
from protocol import consumer_producer
from protocol.protocol_lite import ProtocolLite
from util import variables


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
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    ser = serial.serial_for_url('/dev/ttyS0', baudrate=115200, timeout=20)

    # module_config.config_module()
    consumer_producer.start_send_receive_threads(ser)
    protocol = ProtocolLite()
    protocol.send_message('test')
