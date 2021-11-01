import socket
import time

import serial


class LoRaPerformance:
    MESSAGE_LENGTH = 250

    def __init__(self):
        self.ser = serial.serial_for_url('/dev/ttyS0', baudrate=115200, timeout=60)
        self.ser.flush()
        self.set_module_config()
        time.sleep(1)

    def verify_message(self, verify_list):
        for message in verify_list:
            message_from_module = self.ser.readline()
            if message not in message_from_module:
                raise ValueError(f'{message} != {message_from_module}')

    def send_message(self, length):
        message = b''
        for i in range(0, length):
            message = message + b'a'
        print(str(len(message)).encode())
        self.ser.write(b'AT+SEND=' + str(len(message)).encode() + b'\r\n')
        self.verify_message([b'AT,OK'])
        time.sleep(0.1)
        self.ser.write(message + b'\r\n')
        self.verify_message([b'AT,SENDING', b'AT,SENDED'])

    def set_module_config(self, config=b'AT+CFG=433500000,20,3,10,1,1,0,0,0,0,3000,8,4\r\n'):
        self.ser.write(config)
        print(f'message after setting config: {self.ser.readline()}')
        self.ser.write(b'AT+RX\r\n')
        print(f'message after setting config: {self.ser.readline()}')


class LoRaPerformanceServer(LoRaPerformance):

    def __init__(self, port):
        super().__init__()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(("", port))
        self.conn = None

    def start_server(self):
        self.s.listen(1)
        self.conn = self.s.accept()[0]
        self.send_start_message()
        self.send_message(self.MESSAGE_LENGTH)

    def send_start_message(self):
        self.conn.send(b'START')

    def close_connection(self):
        self.conn.close()
        self.s.close()


class LoRaPerformanceClient(LoRaPerformance):

    def __init__(self, ip, port):
        super().__init__()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        self.port = port

    def start_client(self):
        self.s.connect((self.ip, self.port))
        # after connection to server was established wait for LoRa message
        data = self.s.recv(1024)
        start_time = time.time()
        print(f'received message from server LoRa module: {self.ser.readline()}')
        received_time = time.time()
        print(f'time: {received_time - start_time}s')

        self.s.close()
