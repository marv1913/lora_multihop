import socket
import threading
import time
from queue import Queue

from lora_multihop import serial_connection


class LocalConsumerProducer:

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
        self.connection_list = []

    def start_send_receive_threads(self, is_server=True):
        self.tcp_communication_running = True
        sending_thread = threading.Thread(target=self.start_sending)
        sending_thread.start()
        if is_server:
            connection_listener_thread = threading.Thread(target=self.waiting_for_connections)
            connection_listener_thread.start()
        else:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.socket.setblocking(False)
            self.connection_list.append(self.socket)
            t = threading.Thread(target=self.start_receiving, args=(self.socket,))
            t.start()

    def waiting_for_connections(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)
        self.socket.bind(("", self.port))
        self.socket.listen(2)
        while self.tcp_communication_running:
            try:
                conn, addr = self.socket.accept()
                conn.setblocking(False)
                self.connection_list.append(conn)
                t = threading.Thread(target=self.start_receiving, args=(conn,))
                t.start()
            except socket.error:
                pass
        print('stop waiting for incoming connections')

    def start_receiving(self, connection):
        while self.tcp_communication_running:
            try:
                data = connection.recv(1024)
                if data:
                    print(f'data: {data}')
                    serial_connection.response_q.put(data.decode())
            except socket.error:
                time.sleep(0.2)
        print('receiving thread stopped')

    def start_sending(self):
        while self.tcp_communication_running:
            while not serial_connection.writing_q.empty():
                payload = serial_connection.writing_q.get()[0]
                if 'AT' not in payload:
                    message_to_send = serial_connection.str_to_bytes(f'LR,{self.module_address},10,'+ payload)
                    for connection in self.connection_list:
                        connection.send(message_to_send)
                serial_connection.status_q.put(True)
                time.sleep(0.5)
        print('sending thread stopped')

    def stop_local_consumer_producer(self):
        self.tcp_communication_running = False
        self.socket.close()
