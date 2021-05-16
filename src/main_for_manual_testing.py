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
    msg_as_bytes = 'LR,10,|0100|hällo|'.encode()
    print(msg_as_bytes)
    print(msg_as_bytes.hex())
    print(b'LR,10,|0100|h\xc3\xa4llo|'.decode())
