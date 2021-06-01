import unittest

__author__ = "Marvin Rausch"

import socket

from unittest.mock import patch, MagicMock

from ipc import java_ipc
from protocol import protocol_lite


class JavaIPCTest(unittest.TestCase):

    def test_create_connect_request_message(self):
        self.assertEqual('ConnectRequest,alice,bob,60', java_ipc.create_connect_request_message('alice', 'bob', 60))

    def test_process_registered_peers_request(self):
        socket_mock = MagicMock()
        connection_mock = MagicMock()
        with patch.object(socket, 'socket', return_value=socket_mock), \
        patch.object(protocol_lite.ProtocolLite, 'start_protocol_thread'):
            ipc = java_ipc.JavaIPC(4711, 4712, module_address='0200')
            ipc.listen_for_connections = MagicMock()
            ipc.listen_for_connections.__bool__.side_effect = [True, False]
            ipc.tcp_server_active = MagicMock()
            ipc.tcp_server_active.__bool__.side_effect = [True, False]
            socket_mock.accept.return_value = connection_mock, ''
            data_mock = MagicMock()
            data_mock.decode.return_value = 'registeredPeers?|'
            connection_mock.recv.return_value = data_mock

            ipc.start_tcp_server()
            connection_mock.send.assert_called_with('RegisteredPeers|')

    def test_process_registration_message(self):
        socket_mock = MagicMock()
        connection_mock = MagicMock()
        with patch.object(socket, 'socket', return_value=socket_mock), \
        patch.object(protocol_lite.ProtocolLite, 'start_protocol_thread'), \
                patch.object(protocol_lite.ProtocolLite, 'send_registration_message') as send_registration_message_mocked:
            ipc = java_ipc.JavaIPC(4711, 4712, module_address='0200')
            ipc.listen_for_connections = MagicMock()
            ipc.listen_for_connections.__bool__.side_effect = [True, False]
            ipc.tcp_server_active = MagicMock()
            ipc.tcp_server_active.__bool__.side_effect = [True, False]
            socket_mock.accept.return_value = connection_mock, ''
            data_mock = MagicMock()
            data_mock.decode.return_value = 'Registration,alice,true|'
            connection_mock.recv.return_value = data_mock

            ipc.start_tcp_server()
            send_registration_message_mocked.assert_called_with(True, 'alice')

    def test_process_connect_request_message(self):
        socket_mock = MagicMock()
        connection_mock = MagicMock()
        with patch.object(socket, 'socket', return_value=socket_mock), \
        patch.object(protocol_lite.ProtocolLite, 'start_protocol_thread'), \
                patch.object(protocol_lite.ProtocolLite, 'send_connect_request_header') as send_connect_request_mocked:
            ipc = java_ipc.JavaIPC(4711, 4712, module_address='0200')
            ipc.listen_for_connections = MagicMock()
            ipc.listen_for_connections.__bool__.side_effect = [True, False]
            ipc.tcp_server_active = MagicMock()
            ipc.tcp_server_active.__bool__.side_effect = [True, False]
            socket_mock.accept.return_value = connection_mock, ''
            data_mock = MagicMock()
            data_mock.decode.return_value = 'ConnectRequest,alice,bob,60|'
            connection_mock.recv.return_value = data_mock

            ipc.start_tcp_server()
            send_connect_request_mocked.assert_called_with('alice', 'bob', '60')
