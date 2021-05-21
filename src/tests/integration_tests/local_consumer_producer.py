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
        self.server_socket_thread_second_client = None

        self.inserting_thread_running = False
        self.tcp_communication_running = False

    def start_send_receive_threads(self, is_server=True):
        if is_server:
            t = threading.Thread(target=self.start_tcp_server)
        else:
            t = threading.Thread(target=self.start_tcp_client)
        t.start()

    def start_server_socket(self, port, second_socket=False):
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
                    if second_socket:
                        while not self.send_queue_second_client.empty():
                            payload = self.send_queue_second_client.get()
                            logging.debug(f'send via tcp to client: {payload} to client with port {port}')
                            if 'AT' not in payload:
                                conn.send(consumer_producer.str_to_bytes(f'LR,{self.module_address},10,' + payload))
                    else:
                        while not self.send_queue.empty():
                            payload = self.send_queue.get()
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

    def start_inserting_into_sending_queue(self):
        while self.inserting_thread_running:
            while not consumer_producer.q.empty():
                payload = consumer_producer.q.get()[0]
                logging.debug(f'put into sending queue: {payload}')
                self.send_queue.put(payload)
                if self.port_second_client is not None:
                    logging.debug(f'put into second sending queue: {payload}')
                    self.send_queue_second_client.put(payload)
                consumer_producer.status_q.put(True)

    def start_tcp_server(self):
        self.inserting_thread_running = True
        self.tcp_communication_running = True

        self.sending_queue_inserter_thread = threading.Thread(target=self.start_inserting_into_sending_queue)
        self.server_socket_thread = threading.Thread(target=self.start_server_socket, args=[self.port])

        self.sending_queue_inserter_thread.start()
        self.server_socket_thread.start()

        if self.port_second_client is not None:
            server_socket_thread_second_client = threading.Thread(target=self.start_server_socket,
                                                                  args=[self.port_second_client, True])
            server_socket_thread_second_client.start()

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
        self.inserting_thread_running = False
        self.tcp_communication_running = False
