import socket
import threading
import time
from queue import Queue

from lora_multihop import serial_connection


class LocalNetwork:

    def __init__(self, port, module_address, host=None):
        self.host = host
        self.port = port
        self.module_address = module_address
        self.send_queue = Queue()
        self.send_queue_second_client = Queue()
        self.sending_queue_inserter_thread = None
        self.server_socket_thread = None

        self.tcp_communication_running = False
        self.socket = None

    def start_send_receive_threads(self, is_server=True):
        if is_server:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind(("", self.port))
            self.socket.listen(1)
            conn, addr = self.socket.accept()
            conn.setblocking(False)
            t = threading.Thread(target=self.start_sending_receiving, args=(conn,))
        else:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.socket.setblocking(False)

            t = threading.Thread(target=self.start_sending_receiving, args=(self.socket,))
        self.tcp_communication_running = True

        t.start()

    def start_sending_receiving(self, connection):
        while self.tcp_communication_running:
            try:
                data = connection.recv(2048)
                if data:
                    print(f'data: {data}')
                    serial_connection.response_q.put(data.decode())
            except socket.error:
                time.sleep(0.5)
            while not serial_connection.writing_q.empty():
                payload = serial_connection.writing_q.get()[0]
                if 'AT' not in payload:
                    connection.sendall(serial_connection.str_to_bytes(f'LR,{self.module_address},10,'+ payload))
                serial_connection.status_q.put(True)

    def stop_local_consumer_producer(self):
        self.tcp_communication_running = False
        self.socket.close()
