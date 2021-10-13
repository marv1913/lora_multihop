import threading
import unittest

__author__ = "Marvin Rausch"

import socket

from unittest.mock import patch, MagicMock

from lora_multihop import protocol, ipc


class JavaIPCTest(unittest.TestCase):

    def test_create_connect_request_message(self):
        self.assertEqual('ConnectRequest,alice,bob,60', ipc.create_connect_request_message('alice', 'bob', 60))

    def test_process_registered_peers_request(self):
        socket_mock = MagicMock()
        connection_mock = MagicMock()
        with patch.object(socket, 'socket', return_value=socket_mock), \
                patch.object(protocol.Protocol, 'start_protocol_thread'):
            test_ipc = ipc.IPC(4711, 4712, module_address='0200')
            test_ipc.listen_for_data = MagicMock()
            test_ipc.listen_for_data.__bool__.side_effect = [True, False]
            test_ipc.tcp_server_active = MagicMock()
            test_ipc.tcp_server_active.__bool__.side_effect = [True, False]
            socket_mock.accept.return_value = connection_mock, ''
            data_mock = MagicMock()
            data_mock.decode.return_value = 'registeredPeers?|'
            connection_mock.recv.return_value = data_mock

            test_ipc.start_tcp_server()
            connection_mock.send.assert_called_with(b'RegisteredPeers|')

    def test_process_registration_message(self):
        socket_mock = MagicMock()
        connection_mock = MagicMock()
        with patch.object(socket, 'socket', return_value=socket_mock), \
                patch.object(protocol.Protocol, 'start_protocol_thread'), \
                patch.object(protocol.Protocol,
                             'send_registration_message') as send_registration_message_mocked:
            test_ipc = ipc.IPC(4711, 4712, module_address='0200')
            test_ipc.listen_for_data = MagicMock()
            test_ipc.listen_for_data.__bool__.side_effect = [True, False]
            test_ipc.tcp_server_active = MagicMock()
            test_ipc.tcp_server_active.__bool__.side_effect = [True, False]
            socket_mock.accept.return_value = connection_mock, ''
            data_mock = MagicMock()
            data_mock.decode.return_value = 'Registration,alice,true|'
            connection_mock.recv.return_value = data_mock

            test_ipc.start_tcp_server()
            send_registration_message_mocked.assert_called_with(True, 'alice')

    def test_process_connect_request_message(self):
        socket_mock = MagicMock()
        connection_mock = MagicMock()
        with patch.object(socket, 'socket', return_value=socket_mock), \
                patch.object(protocol.Protocol, 'start_protocol_thread'), \
                patch.object(protocol.Protocol, 'send_connect_request_header') as send_connect_request_mocked:
            test_ipc = ipc.IPC(4711, 4712, module_address='0200')
            test_ipc.listen_for_data = MagicMock()
            test_ipc.listen_for_data.__bool__.side_effect = [True, False]
            test_ipc.tcp_server_active = MagicMock()
            test_ipc.tcp_server_active.__bool__.side_effect = [True, False]
            socket_mock.accept.return_value = connection_mock, ''
            data_mock = MagicMock()
            data_mock.decode.return_value = 'ConnectRequest,alice,bob,60|'
            connection_mock.recv.return_value = data_mock

            test_ipc.start_tcp_server()
            send_connect_request_mocked.assert_called_with('alice', 'bob', '60')

    def test_send_ipc_message_to_java_side(self):
        socket_mock = MagicMock()
        connection_mock = MagicMock()
        with patch.object(socket, 'socket', return_value=socket_mock), \
                patch.object(protocol.Protocol, 'start_protocol_thread'):
            test_ipc = ipc.IPC(4711, 4712, module_address='0200')
            test_ipc.listen_for_data = MagicMock()
            test_ipc.listen_for_data.__bool__.side_effect = [True, False]
            test_ipc.tcp_server_active = MagicMock()
            test_ipc.tcp_server_active.__bool__.side_effect = [True, False]
            socket_mock.accept.return_value = connection_mock, ''
            data_mock = MagicMock()
            data_mock.decode.side_effect = socket.timeout
            connection_mock.recv.return_value = data_mock
            test_ipc.protocol.sending_queue.put('test')

            test_ipc.start_tcp_server()
            connection_mock.send.assert_called_with(b'test|')

    def test_process_registration_message_bad_socket_timeout(self):
        socket_mock = MagicMock()
        with patch.object(socket, 'socket', return_value=socket_mock), \
                patch.object(protocol.Protocol, 'start_protocol_thread'):
            test_ipc = ipc.IPC(4711, 4712, module_address='0200')
            test_ipc.listen_for_data = MagicMock()
            test_ipc.listen_for_data.__bool__.side_effect = [True, False]
            test_ipc.tcp_server_active = MagicMock()
            test_ipc.tcp_server_active.__bool__.side_effect = [True, False]
            socket_mock.accept.side_effect = socket.timeout

            test_ipc.start_tcp_server()

    def test_process_registration_message_bad_connection_reset_error(self):
        socket_mock = MagicMock()
        with patch.object(socket, 'socket', return_value=socket_mock), \
                patch.object(protocol.Protocol, 'start_protocol_thread'):
            test_ipc = ipc.IPC(4711, 4712, module_address='0200')
            test_ipc.listen_for_data = MagicMock()
            test_ipc.listen_for_data.__bool__.side_effect = [True, False]
            test_ipc.tcp_server_active = MagicMock()
            test_ipc.tcp_server_active.__bool__.side_effect = [True, False]
            socket_mock.accept.side_effect = ConnectionResetError

            test_ipc.start_tcp_server()

    def test_process_registration_message_bad_broken_pipe_error(self):
        socket_mock = MagicMock()
        connection_mock = MagicMock()
        with patch.object(socket, 'socket', return_value=socket_mock), \
                patch.object(protocol.Protocol, 'start_protocol_thread'):
            test_ipc = ipc.IPC(4711, 4712, module_address='0200')
            test_ipc.listen_for_data = MagicMock()
            test_ipc.listen_for_data.__bool__.side_effect = [True, False]

            socket_mock.accept.return_value = connection_mock, ''
            data_mock = MagicMock()
            data_mock.decode.side_effect = BrokenPipeError
            connection_mock.recv.return_value = data_mock
            test_ipc.tcp_server_active = True

            test_ipc.start_tcp_server()

    def test_process_session_message_from_java_side(self):
        socket_mock = MagicMock()
        connection_mock = MagicMock()
        message = 'hello world'
        with patch.object(socket, 'socket', return_value=socket_mock), \
                patch.object(protocol.Protocol, 'start_protocol_thread'), \
                patch.object(protocol.Protocol, 'send_message') as send_message_mocked:
            test_ipc = ipc.IPC(4711, 4712, module_address='0200')
            test_ipc.listen_for_data = MagicMock()
            test_ipc.listen_for_data.__bool__.side_effect = [True, False]

            socket_mock.accept.return_value = connection_mock, ''
            connection_mock.recv.return_value = message

            test_ipc.start_tcp_server_for_message_transfer()
            send_message_mocked.assert_called_with(message)

    def test_send_received_session_message_to_java_side(self):
        socket_mock = MagicMock()
        connection_mock = MagicMock()
        with patch.object(socket, 'socket', return_value=socket_mock), \
                patch.object(protocol.Protocol, 'start_protocol_thread'), \
                patch.object(protocol.Protocol, 'send_message'):
            test_ipc = ipc.IPC(4711, 4712, module_address='0200')
            test_ipc.listen_for_data = MagicMock()
            test_ipc.listen_for_data.__bool__.side_effect = [True, False]

            socket_mock.accept.return_value = connection_mock, ''
            connection_mock.recv.return_value = 'hello'
            test_ipc.protocol.received_messages_queue.put(b'hello world')

            test_ipc.start_tcp_server_for_message_transfer()
            connection_mock.send.assert_called_with(b'hello world')

    def test_process_session_message_from_java_side_edge_empty_message(self):
        socket_mock = MagicMock()
        connection_mock = MagicMock()
        with patch.object(socket, 'socket', return_value=socket_mock), \
                patch.object(protocol.Protocol, 'start_protocol_thread'), \
                patch.object(protocol.Protocol, 'send_message'):
            test_ipc = ipc.IPC(4711, 4712, module_address='0200')

            socket_mock.accept.return_value = connection_mock, ''
            connection_mock.recv.return_value = ''

            test_ipc.start_tcp_server_for_message_transfer()

    def test_start_ipc(self):
        with patch.object(threading, 'Thread'):
            test_ipc = ipc.IPC(4711, 4712, module_address='0200')
            test_ipc.start_ipc()
            test_ipc.ipc_tcp_server_thread.start.assert_called()
            test_ipc.message_transfer_thread.start.assert_called()

    def test_stop_test_ipc(self):
        with patch.object(protocol.Protocol, 'start_protocol_thread'):
            test_ipc = ipc.IPC(4711, 4712, module_address='0200')
            test_ipc.protocol = MagicMock()
            test_ipc.listen_for_data = True
            test_ipc.tcp_server_active = True

            test_ipc.stop_ipc_instance()

            self.assertFalse(test_ipc.listen_for_data)
            self.assertFalse(test_ipc.tcp_server_active)
            test_ipc.protocol.stop.assert_called_once()
