import threading
import unittest

__author__ = "Marvin Rausch"

import socket

from unittest.mock import patch, MagicMock

from lora_multihop import ipc, protocol_lite


class JavaIPCTest(unittest.TestCase):

    def test_create_connect_request_message(self):
        self.assertEqual('ConnectRequest,alice,bob,60', ipc.create_connect_request_message('alice', 'bob', 60))

    def test_process_registered_peers_request(self):
        socket_mock = MagicMock()
        connection_mock = MagicMock()
        with patch.object(socket, 'socket', return_value=socket_mock), \
                patch.object(protocol_lite.ProtocolLite, 'start_protocol_thread'):
            ipc = ipc.JavaIPC(4711, 4712, module_address='0200')
            ipc.listen_for_connections = MagicMock()
            ipc.listen_for_connections.__bool__.side_effect = [True, False]
            ipc.tcp_server_active = MagicMock()
            ipc.tcp_server_active.__bool__.side_effect = [True, False]
            socket_mock.accept.return_value = connection_mock, ''
            data_mock = MagicMock()
            data_mock.decode.return_value = 'registeredPeers?|'
            connection_mock.recv.return_value = data_mock

            ipc.start_tcp_server()
            connection_mock.send.assert_called_with(b'RegisteredPeers|')

    def test_process_registration_message(self):
        socket_mock = MagicMock()
        connection_mock = MagicMock()
        with patch.object(socket, 'socket', return_value=socket_mock), \
                patch.object(protocol_lite.ProtocolLite, 'start_protocol_thread'), \
                patch.object(protocol_lite.ProtocolLite,
                             'send_registration_message') as send_registration_message_mocked:
            ipc = ipc.JavaIPC(4711, 4712, module_address='0200')
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
            ipc = ipc.JavaIPC(4711, 4712, module_address='0200')
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

    def test_send_ipc_message_to_java_side(self):
        socket_mock = MagicMock()
        connection_mock = MagicMock()
        with patch.object(socket, 'socket', return_value=socket_mock), \
                patch.object(protocol_lite.ProtocolLite, 'start_protocol_thread'):
            ipc = ipc.JavaIPC(4711, 4712, module_address='0200')
            ipc.listen_for_connections = MagicMock()
            ipc.listen_for_connections.__bool__.side_effect = [True, False]
            ipc.tcp_server_active = MagicMock()
            ipc.tcp_server_active.__bool__.side_effect = [True, False]
            socket_mock.accept.return_value = connection_mock, ''
            data_mock = MagicMock()
            data_mock.decode.side_effect = socket.timeout
            connection_mock.recv.return_value = data_mock
            ipc.protocol.sending_queue.put('test')

            ipc.start_tcp_server()
            connection_mock.send.assert_called_with(b'test|')

    def test_process_registration_message_bad_socket_timeout(self):
        socket_mock = MagicMock()
        with patch.object(socket, 'socket', return_value=socket_mock), \
                patch.object(protocol_lite.ProtocolLite, 'start_protocol_thread'):
            ipc = ipc.JavaIPC(4711, 4712, module_address='0200')
            ipc.listen_for_connections = MagicMock()
            ipc.listen_for_connections.__bool__.side_effect = [True, False]
            ipc.tcp_server_active = MagicMock()
            ipc.tcp_server_active.__bool__.side_effect = [True, False]
            socket_mock.accept.side_effect = socket.timeout

            ipc.start_tcp_server()

    def test_process_registration_message_bad_connection_reset_error(self):
        socket_mock = MagicMock()
        with patch.object(socket, 'socket', return_value=socket_mock), \
                patch.object(protocol_lite.ProtocolLite, 'start_protocol_thread'):
            ipc = ipc.JavaIPC(4711, 4712, module_address='0200')
            ipc.listen_for_connections = MagicMock()
            ipc.listen_for_connections.__bool__.side_effect = [True, False]
            ipc.tcp_server_active = MagicMock()
            ipc.tcp_server_active.__bool__.side_effect = [True, False]
            socket_mock.accept.side_effect = ConnectionResetError

            ipc.start_tcp_server()

    def test_process_registration_message_bad_broken_pipe_error(self):
        socket_mock = MagicMock()
        connection_mock = MagicMock()
        with patch.object(socket, 'socket', return_value=socket_mock), \
                patch.object(protocol_lite.ProtocolLite, 'start_protocol_thread'):
            ipc = ipc.JavaIPC(4711, 4712, module_address='0200')
            ipc.listen_for_connections = MagicMock()
            ipc.listen_for_connections.__bool__.side_effect = [True, False]

            socket_mock.accept.return_value = connection_mock, ''
            data_mock = MagicMock()
            data_mock.decode.side_effect = BrokenPipeError
            connection_mock.recv.return_value = data_mock
            ipc.tcp_server_active = True

            ipc.start_tcp_server()

    def test_process_session_message_from_java_side(self):
        socket_mock = MagicMock()
        connection_mock = MagicMock()
        message = 'hello world'
        with patch.object(socket, 'socket', return_value=socket_mock), \
                patch.object(protocol_lite.ProtocolLite, 'start_protocol_thread'), \
                patch.object(protocol_lite.ProtocolLite, 'send_message') as send_message_mocked:
            ipc = ipc.JavaIPC(4711, 4712, module_address='0200')
            ipc.listen_for_connections = MagicMock()
            ipc.listen_for_connections.__bool__.side_effect = [True, False]

            socket_mock.accept.return_value = connection_mock, ''
            connection_mock.recv.return_value = message

            ipc.start_tcp_server_for_message_transfer()
            send_message_mocked.assert_called_with(message)

    def test_send_received_session_message_to_java_side(self):
        socket_mock = MagicMock()
        connection_mock = MagicMock()
        with patch.object(socket, 'socket', return_value=socket_mock), \
                patch.object(protocol_lite.ProtocolLite, 'start_protocol_thread'), \
                patch.object(protocol_lite.ProtocolLite, 'send_message'):
            ipc = ipc.JavaIPC(4711, 4712, module_address='0200')
            ipc.listen_for_connections = MagicMock()
            ipc.listen_for_connections.__bool__.side_effect = [True, False]

            socket_mock.accept.return_value = connection_mock, ''
            connection_mock.recv.return_value = 'hello'
            ipc.protocol.received_messages_queue.put(b'hello world')

            ipc.start_tcp_server_for_message_transfer()
            connection_mock.send.assert_called_with(b'hello world')

    def test_process_session_message_from_java_side_edge_empty_message(self):
        socket_mock = MagicMock()
        connection_mock = MagicMock()
        with patch.object(socket, 'socket', return_value=socket_mock), \
                patch.object(protocol_lite.ProtocolLite, 'start_protocol_thread'), \
                patch.object(protocol_lite.ProtocolLite, 'send_message'):
            ipc = ipc.JavaIPC(4711, 4712, module_address='0200')

            socket_mock.accept.return_value = connection_mock, ''
            connection_mock.recv.return_value = ''

            ipc.start_tcp_server_for_message_transfer()

    def test_start_ipc(self):
        with patch.object(threading, 'Thread'):
            ipc = ipc.JavaIPC(4711, 4712, module_address='0200')
            ipc.start_ipc()
            ipc.ipc_tcp_server_thread.start.assert_called()
            ipc.message_transfer_thread.start.assert_called()

    def test_stop_ipc(self):
        with patch.object(protocol_lite.ProtocolLite, 'start_protocol_thread'):
            ipc = ipc.JavaIPC(4711, 4712, module_address='0200')
            ipc.protocol = MagicMock()
            ipc.listen_for_connections = True
            ipc.tcp_server_active = True

            ipc.stop_ipc_instance()

            self.assertFalse(ipc.listen_for_connections)
            self.assertFalse(ipc.tcp_server_active)
            ipc.protocol.stop.assert_called_once()
