import logging

import serial

from lora_multihop import serial_connection
from lora_multihop.protocol import Protocol


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
    serial_connection.start_send_receive_threads(ser)
    protocol = Protocol()
    protocol.send_message('test')
