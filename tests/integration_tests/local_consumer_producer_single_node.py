import socket
import threading
import time
from queue import Queue

from lora_multihop import consumer_producer


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
                    consumer_producer.response_q.put(data)
            except socket.error:
                time.sleep(0.5)
            while not consumer_producer.q.empty():
                payload = consumer_producer.q.get()[0]
                if b'AT' not in payload:
                    connection.sendall(consumer_producer.str_to_bytes(f'LR,{self.module_address},10,') + payload)
                consumer_producer.status_q.put(True)

    def stop_local_consumer_producer(self):
        self.tcp_communication_running = False
        self.socket.close()
