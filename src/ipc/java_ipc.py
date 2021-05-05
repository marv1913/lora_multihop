import logging
import os
import socket
import threading

from ipc import xml
from protocol import consumer_producer
from protocol.protocol_lite import ProtocolLite
from util import variables


class JavaIPC:

    def __init__(self):
        self.listen_for_connections = True
        variables.MY_ADDRESS = consumer_producer.get_current_address_from_module()
        logging.info('loaded address of module: {}'.format(variables.MY_ADDRESS))
        self.protocol = ProtocolLite()
        self.protocol.start_protocol_thread()
        self.connection = None
        threading.Thread(target=self.start_tcp_server_for_message_transfer).start()

    def start_tcp_server_for_message_transfer(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 6200))
        s.listen(1)
        conn, addr = s.accept()
        conn.settimeout(1)
        while self.listen_for_connections:
            try:
                data = conn.recv(1024)
                print(f'data: {data}')
                self.protocol.send_message(data)
                if not data:
                    conn.close()
                    print('closed')
                    break
            except socket.timeout:
                if not self.protocol.received_messages_queue.empty():
                    logging.debug('send message via rpc to java side')
                    conn.send(str.encode(self.protocol.received_messages_queue.get()))

    def start_tcp_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 6100))
        s.listen(1)
        try:
            while self.listen_for_connections:
                conn, addr = s.accept()
                self.connection = conn
                while True:
                    conn.settimeout(1)
                    try:
                        data = conn.recv(1024)
                        print(f'data: {data}')
                        if not data:
                            conn.close()
                            print('closed')
                            break
                        if data.decode() == 'registeredPeers?':
                            print(self.protocol.routing_table.get_peers())
                            conn.send(
                                xml.get_available_peers_as_xml_str(self.protocol.routing_table.get_peers()) + b'|')
                        else:
                            root = xml.parse_xml(data)
                            if root.tag == 'registrationModel':
                                registration_message_parameter = xml.parse_registration_message_from_xml(root)
                                self.protocol.send_registration_message(registration_message_parameter[0],
                                                                        registration_message_parameter[1])
                            elif root.tag == 'connection_request':
                                route_request_parameter = xml.parse_connect_request_from_xml(root)
                                self.protocol.send_connect_request_header(route_request_parameter[0],
                                                                          route_request_parameter[1],
                                                                          route_request_parameter[2])
                    except socket.timeout:
                        while not self.protocol.sending_queue.empty():
                            payload = self.protocol.sending_queue.get()
                            logging.debug(f'sending: {payload}')
                            conn.send(payload + b'|')

        finally:
            s.close()

    def send_message_to_java_client(self, message):
        self.sending_queue.put(message)

    def listen_for_exit(self):
        command = input()
        print(f'read command: {command}')
        if command == 'exit':
            print('exit')
            self.listen_for_connections = False
            self.protocol.stop()
            os._exit(0)
