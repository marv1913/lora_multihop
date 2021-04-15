import logging
import time

import serial

import protocol.consumer_producer
from messenger import messenger
from protocol.protocol_lite import ProtocolLite


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
    # module_conf = ModuleConfig(consumer_producer.ser)
    # module_conf.config_module()
    protocol.consumer_producer.start_send_receive_threads(ser)

    protocol = ProtocolLite()

    messenger = messenger.Messenger(protocol)
    time.sleep(2)

    messenger.start_chatting()

    # TODO implement function to config lora module before launching UI and get own address from module
