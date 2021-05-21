import logging
import socket
import threading

from ipc import xml
from protocol import consumer_producer
from protocol.protocol_lite import ProtocolLite
from util import variables


class JavaIPC:

    def __init__(self, ipc_port, message_port, module_address=None):
        self.listen_for_connections = True
        if module_address is None:
            variables.MY_ADDRESS = consumer_producer.get_current_address_from_module()
            logging.info('loaded address of module: {}'.format(variables.MY_ADDRESS))
        else:
            variables.MY_ADDRESS = module_address
        self.protocol = ProtocolLite()
        self.protocol.start_protocol_thread()
        self.connection = None
        self.ipc_port = ipc_port
        self.message_port = message_port
        self.tcp_server_active = False

        self.message_transfer_thread = None
        self.ipc_tcp_server_thread = None

    def start_tcp_server_for_message_transfer(self):
        client_connected = False
        while not client_connected and self.listen_for_connections:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.bind(("", self.message_port))
                s.listen(1)
                conn, addr = s.accept()
                conn.settimeout(1)
                client_connected = True
            except socket.timeout:
                pass
        while self.listen_for_connections:
            try:
                data = conn.recv(1024)
                print(f'data: {data}')
                if len(data) > 0:
                    self.protocol.send_message(consumer_producer.bytes_to_str(data))
                if not data:
                    conn.close()
                    print('closed')
                    break
            except socket.timeout:
                if not self.protocol.received_messages_queue.empty():
                    received_message = self.protocol.received_messages_queue.get()
                    message = str.encode(received_message)
                    logging.debug(f'send message via rpc to java side: {message}')
                    conn.send(message)

    def start_tcp_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", self.ipc_port))
        s.listen(1)
        self.tcp_server_active = True
        try:
            while self.listen_for_connections:
                try:
                    s.settimeout(2)
                    conn, addr = s.accept()
                    self.connection = conn
                    logging.debug(f'connected to java ipc with address {addr}')
                    while self.tcp_server_active:
                        conn.settimeout(1)
                        try:
                            data = conn.recv(1024)
                            print(f'data: {data}')
                            if not data:
                                conn.close()
                                print('closed')
                                break
                            received_data_as_list = data.decode().split(variables.HEADER_DELIMITER)
                            for message in received_data_as_list:
                                if message == 'registeredPeers?':
                                    registered_peers = self.protocol.routing_table.get_peers()
                                    logging.debug(f'send registered peer to java: {registered_peers}')
                                    conn.send(xml.get_available_peers_as_xml_str(registered_peers) + b'|')
                                elif len(message) != 0:
                                    logging.debug(f'xml message: {message}')
                                    root = xml.parse_xml(message.encode())
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
                        except BrokenPipeError:
                            logging.debug('connection reset by client')
                            break
                except socket.timeout:
                    pass
                except ConnectionResetError:
                    logging.debug('Connection reset by client. Wait for new connection')
        finally:
            logging.debug('java ipc: tcp server socket closed')
            s.close()

    def start_ipc(self):
        self.message_transfer_thread = threading.Thread(target=self.start_tcp_server_for_message_transfer)
        self.message_transfer_thread.start()

        self.ipc_tcp_server_thread = threading.Thread(target=self.start_tcp_server)
        self.ipc_tcp_server_thread.start()

    def stop_ipc_instance(self):
        self.listen_for_connections = False
        self.tcp_server_active = False
        self.protocol.stop()
