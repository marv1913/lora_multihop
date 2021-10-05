import logging
import socket
import threading

from lora_multihop import protocol_lite, serial_connection, variables, module_config


class JavaIPC:

    def __init__(self, ipc_port, message_port, module_address=None):
        self.listen_for_connections = True
        if module_address is None:
            variables.MY_ADDRESS = module_config.get_current_address()
            logging.info('loaded address of module: {}'.format(variables.MY_ADDRESS))
        else:
            variables.MY_ADDRESS = module_address
        self.protocol = protocol_lite.ProtocolLite()
        self.protocol.start_protocol_thread()
        self.connection = None
        self.ipc_port = ipc_port
        self.message_port = message_port
        self.tcp_server_active = False

        self.message_transfer_thread = None
        self.ipc_tcp_server_thread = None

    def start_tcp_server_for_message_transfer(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", self.message_port))
        s.listen(1)
        conn, addr = s.accept()
        print('client for message transfer connected')
        conn.setblocking(False)

        while self.listen_for_connections:
            try:
                data = conn.recv(220)
                print(f'data: {data}')
                if len(data) > 0:
                    self.protocol.send_message(data)
                if not data:
                    conn.close()
                    print('closed message socket')
                    break
            except socket.error:
                pass
            if not self.protocol.received_messages_queue.empty():
                message = self.protocol.received_messages_queue.get()
                logging.debug(f'send message via rpc to java side: {message}')
                conn.send(message)

    def start_tcp_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", self.ipc_port))
        s.listen(1)
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
                                    message = 'RegisteredPeers'
                                    for i in range(0, len(registered_peers)):
                                        message = message + ',' + registered_peers[i]['peer_id']
                                    logging.debug(f'send registered peer to java: {registered_peers}')
                                    conn.send((message + '|').encode(variables.ENCODING))
                                elif len(message) != 0:
                                    logging.debug(f'request from java side: {message}')
                                    message_values = message.split(variables.JAVA_IPC_MESSAGE_VALUES_DELIMITER)
                                    message_type = message_values[0]
                                    if message_type == 'Registration':
                                        subscribe_str = message_values[2]
                                        if subscribe_str.lower() == 'true':
                                            subscribe = True
                                        else:
                                            subscribe = False
                                        self.protocol.send_registration_message(subscribe, message_values[1])
                                    elif message_type == 'ConnectRequest':
                                        self.protocol.send_connect_request_header(message_values[1], message_values[2],
                                                                                  message_values[3])
                                    elif message_type == 'DisconnectRequest':
                                        self.protocol.send_disconnect_request_header(message_values[1],
                                                                                     message_values[2])
                        except socket.timeout:
                            while not self.protocol.sending_queue.empty():
                                payload = self.protocol.sending_queue.get()
                                logging.debug(f'sending: {payload}')
                                conn.send((payload + '|').encode(variables.ENCODING))
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
        self.tcp_server_active = True
        self.ipc_tcp_server_thread.start()

    def stop_ipc_instance(self):
        self.listen_for_connections = False
        self.tcp_server_active = False
        self.protocol.stop()


def create_connect_request_message(source_peer_id, target_peer_id, timeout):
    return f'ConnectRequest,{source_peer_id},{target_peer_id},{timeout}'


def create_disconnect_request_message(source_peer_id, target_peer_id):
    return f'DisconnectRequest,{source_peer_id},{target_peer_id}'
