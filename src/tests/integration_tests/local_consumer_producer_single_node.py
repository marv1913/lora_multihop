import logging
import socket
import threading
from queue import Queue

from protocol import consumer_producer


class LocalConsumerProducer:

    def __init__(self, port, module_address, host=None, port_second_client=None):
        self.host = host
        self.port = port
        self.port_second_client = port_second_client
        self.module_address = module_address
        self.send_queue = Queue()
        self.send_queue_second_client = Queue()
        self.sending_queue_inserter_thread = None
        self.server_socket_thread = None

        self.tcp_communication_running = False

    def start_send_receive_threads(self, is_server=True):
        if is_server:
            t = threading.Thread(target=self.start_tcp_server)
        else:
            t = threading.Thread(target=self.start_tcp_client)
        t.start()

    def start_server_socket(self, port):
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind(("", port))
                s.settimeout(1)
                s.listen(1)
                conn, addr = s.accept()
                logging.debug(f'client on port {port} connected')
                while True:
                    try:
                        conn.settimeout(1)
                        data = conn.recv(1024)
                        if data:
                            print(f'data: {data}')
                            data = data.decode()
                            consumer_producer.response_q.put(data)
                    except socket.timeout:
                        pass
                    if not self.tcp_communication_running:
                        break
                    while not consumer_producer.q.empty():
                        payload = consumer_producer.q.get()[0]
                        logging.debug(f'send via tcp to client: {payload} to client with port {port}')
                        if 'AT' not in payload:
                            conn.send(consumer_producer.str_to_bytes(f'LR,{self.module_address},10,' + payload))
                conn.close()
                s.shutdown(1)
                s.close()
                return
            except socket.timeout:
                if not self.tcp_communication_running:
                    break

    def start_tcp_server(self):
        self.tcp_communication_running = True

        self.server_socket_thread = threading.Thread(target=self.start_server_socket, args=[self.port])
        self.server_socket_thread.start()

    def start_tcp_client(self):
        self.tcp_communication_running = True
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.connect((self.host, self.port))
            while True:
                try:
                    data = s.recv(1024)
                    if data:
                        print(f'data: {data}')
                        data = data.decode()
                        consumer_producer.response_q.put(data)
                except socket.timeout:
                    pass
                if not self.tcp_communication_running:
                    break
                while not consumer_producer.q.empty():
                    payload = consumer_producer.q.get()[0]
                    if 'AT' not in payload:
                        s.sendall(consumer_producer.str_to_bytes(f'LR,{self.module_address},10,' + payload))
                    consumer_producer.status_q.put(True)
        logging.debug("local consumer producer disconnected")

    def stop_local_consumer_producer(self):
        self.tcp_communication_running = False
