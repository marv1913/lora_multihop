import threading
import queue
import time
import logging

from lora_multihop import variables

__author__ = "Marvin Rausch"

ser = None

logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-9s) %(message)s', )

BUF_SIZE = 100
writing_q = queue.Queue(BUF_SIZE)
BUF_SIZE = 1000
response_q = queue.Queue(BUF_SIZE)
BUF_SIZE = 1000
status_q = queue.Queue(BUF_SIZE)
WRITE_DATA = False
READING_THREAD_ACTIVE = True
WRITING_THREAD_ACTIVE = True


def bytes_to_str(message_in_bytes):
    """
    converts bytes to string
    :param message_in_bytes: bytes which should be convert
    :return: decoded bytes as string using decoding defined under variables.ENCODING
    """
    return message_in_bytes.decode(variables.ENCODING)


def str_to_bytes(string_to_convert):
    """
    encodes string to bytes
    :param string_to_convert: string which should be encoded
    :return: encoded string as bytes using encoding defined under variables.ENCODING
    """
    return bytes(string_to_convert, variables.ENCODING)


class ReadingThread(threading.Thread):
    def __init__(self, name):
        super(ReadingThread, self).__init__()
        self.name = name

    def run(self):
        """
        starts a thread for reading messages from serial port
        """
        global READING_THREAD_ACTIVE
        while READING_THREAD_ACTIVE:
            global WRITE_DATA
            if writing_q.empty() and not WRITE_DATA:
                if ser.in_waiting:
                    received_raw_message = ser.readline()
                    logging.debug('received: {}'.format(received_raw_message))
                    try:
                        received_raw_message = bytes_to_str(received_raw_message)
                        response_q.put(received_raw_message)
                    except UnicodeDecodeError:
                        logging.debug(f"message '{received_raw_message}' dumped. because it is not encoded in UTF-8")


class WritingThread(threading.Thread):
    def __init__(self, name):
        super(WritingThread, self).__init__()
        self.name = name
        return

    def run(self):
        """
        starts a thread for writing messages to a serial port
        """
        global WRITING_THREAD_ACTIVE
        while WRITING_THREAD_ACTIVE:
            if not writing_q.empty():
                global WRITE_DATA
                WRITE_DATA = True
                command_tuple = writing_q.get()
                command = command_tuple[0]
                command = command + '\r\n'
                command = str_to_bytes(command)
                verify_list = command_tuple[1]
                logging.debug("sending command '{}'".format(command))
                ser.write(command)
                successful = True
                if len(verify_list) > 0:
                    for entry in verify_list:
                        status = bytes_to_str(ser.readline())
                        status = status.strip()
                        if 'LR' in status:
                            logging.warning('got message while verifying command: {}. Message dumped.'.format(status))
                            #  dump message, if receiving message while verifying status of command
                            status = bytes_to_str(ser.readline())
                            status = status.strip()
                        if entry != status:
                            logging.warning(
                                'could not verify {expected} != {status}'.format(expected=entry, status=status))
                            successful = False
                        else:
                            logging.debug('verified {status}'.format(status=status))
                    status_q.put(successful)

                time.sleep(0.2)
                WRITE_DATA = False


def start_send_receive_threads(serial_conn):
    """
    starts threads for communication with serial port
    :param serial_conn: object for serial connection from pyserial library
    """
    global ser
    ser = serial_conn
    t1 = ReadingThread(name='producer')
    t2 = WritingThread(name='consumer')

    t1.start()
    time.sleep(0.5)
    t2.start()
    time.sleep(0.5)


def execute_command(command_as_str, verification_list=None):
    """
    helper function to send AT-command to serial port
    :param command_as_str: command which should be sent
    :param verification_list: list of expected results; can also be empty if result of command should not be verified
    :return: True if expected results equal to results received from serial port, else False
    """
    if verification_list is None:
        verification_list = []
    writing_q.put((command_as_str, verification_list))
    if len(verification_list) != 0:
        return status_q.get(timeout=variables.COMMAND_VERIFICATION_TIMEOUT)


if __name__ == '__main__':
    p = ReadingThread(name='producer')
    c = WritingThread(name='consumer')

    p.start()
    time.sleep(0.5)
    c.start()
    time.sleep(0.5)
    writing_q.put(('AT', ['AT,OK']))
    writing_q.put(('AT', []))

    time.sleep(2)
    print(response_q.get())
