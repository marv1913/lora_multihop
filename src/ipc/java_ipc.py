import logging

from ipc import xml
from protocol import consumer_producer
from protocol.protocol_lite import ProtocolLite
from util import variables


class JavaIPC:

    def __init__(self, protocol_obj):
        variables.MY_ADDRESS = consumer_producer.get_current_address_from_module()
        logging.info('loaded address of module: {}'.format(variables.MY_ADDRESS))
        self.protocol = protocol_obj
        self.protocol.start_protocol_thread()

    def start_tcp_server(self):
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 6100))
        s.listen(1)
        try:
            while True:
                conn, addr = s.accept()
                while True:
                    data = conn.recv(1024)
                    print(data)
                    if not data:
                        conn.close()
                        print('closed')
                        break
                    if data.decode() == 'registeredPeers?':
                        print(self.protocol.routing_table.get_peers())
                        conn.send(xml.get_available_peers_as_xml_str(self.protocol.routing_table.get_peers()) + b'|')
                    else:
                        root = xml.parse_xml(data)
                        if root.tag == 'registrationModel':
                            registration_message_parameter = xml.parse_registration_message_from_xml(root)
                            self.protocol.send_registration_message(registration_message_parameter[0],
                                                                    registration_message_parameter[1])
        finally:
            s.close()
