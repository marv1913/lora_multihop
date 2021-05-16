import logging
import socket
import threading

from protocol import consumer_producer


class LocalConsumerProducer:

    def __init__(self, port, module_address, host=None):
        self.host = host
        self.port = port
        self.module_address = module_address

    def start_send_receive_threads(self, is_server=True):
        if is_server:
            t = threading.Thread(target=self.start_tcp_server)
        else:
            t = threading.Thread(target=self.start_tcp_client)
        t.start()

    def start_tcp_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", self.port))
        s.listen(1)
        conn, addr = s.accept()
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
            while not consumer_producer.q.empty():
                payload = consumer_producer.q.get()[0]
                logging.debug(payload)
                if 'AT' not in payload:
                    conn.send(consumer_producer.str_to_bytes(f'LR,{self.module_address},10,' + payload))
                consumer_producer.status_q.put(True)

    def start_tcp_client(self):
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
                while not consumer_producer.q.empty():
                    payload = consumer_producer.q.get()[0]
                    if 'AT' not in payload:
                        s.sendall(consumer_producer.str_to_bytes(f'LR,{self.module_address},10,' + payload))
                    consumer_producer.status_q.put(True)

