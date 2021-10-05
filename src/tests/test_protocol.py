import base64
import time
import unittest
from unittest.mock import patch, call, MagicMock

from lora_multihop import protocol_lite, serial_connection, header, variables
from lora_multihop.header import RegistrationHeader, ConnectRequestHeader
from lora_multihop.routing_table import RoutingTable


class ProtocolTest(unittest.TestCase):

    def setUp(self):
        self.protocol = protocol_lite.ProtocolLite()
        variables.MY_ADDRESS = '0130'

    def test_get_best_route_for_destination_good(self):
        with patch.object(protocol_lite.ProtocolLite, 'send_header'):
            raw_message = 'LR,0133,16,|0131|2|5|0133|99fc8d|'
            header_obj = header.create_header_obj_from_raw_message(raw_message)
            self.protocol.process_ack_header(header_obj)
            self.assertEqual('|0131|2|4|0133|99fc8d|', header_obj.get_header_str())

    def test_process_registration_message_header_good_subscribe(self):
        registration_message_header_obj = RegistrationHeader(None, '0131', 5, True, 'testPeer')
        with patch.object(protocol_lite.ProtocolLite, 'send_header') as send_header_mocked:
            self.protocol.process_registration_header(registration_message_header_obj)
            send_header_mocked.assert_called_with('|0131|6|4|true|testPeer|')
            self.assertEqual(1, len(self.protocol.routing_table.available_peers))

    def test_process_registration_message_header_good_unsubscribe(self):
        registration_message_header_obj = RegistrationHeader(None, '0131', 5, True, 'testPeer')
        registration_message_header_obj_unsubscribe = RegistrationHeader(None, '0131', 5, False, 'testPeer')
        variables.PROCESSED_ROUTE_REQUEST_TIMEOUT = 0

        with patch.object(protocol_lite.ProtocolLite, 'send_header') as send_header_mocked:
            self.protocol.process_registration_header(registration_message_header_obj)
            self.protocol.process_registration_header(registration_message_header_obj_unsubscribe)

            self.assertEqual(2, send_header_mocked.call_count)
            self.assertEqual(0, len(self.protocol.routing_table.available_peers))
        variables.PROCESSED_ROUTE_REQUEST_TIMEOUT = 8

    def test_process_registration_message_header_bad_own_message(self):
        registration_message_header_obj = RegistrationHeader(None, '0130', 0, True, 'testPeer')
        with patch.object(protocol_lite.ProtocolLite, 'send_header') as send_header_mocked:
            self.protocol.process_registration_header(registration_message_header_obj)

            self.assertEqual(0, send_header_mocked.call_count)

    def test_process_connect_request_header_good(self):
        variables.MY_ADDRESS = '0201'
        connect_request_header_obj = ConnectRequestHeader('0200', '0200', 5, '0201', '0201', 'test1', 'test2', '2')
        self.protocol.process_connect_request_header(connect_request_header_obj)

    def test_process_connect_request_header_good_forwarding(self):
        variables.MY_ADDRESS = '0201'
        connect_request_header_obj = ConnectRequestHeader('0200', '0200', 5, '0202', '0201', 'test1', 'test2', '2')
        with patch.object(RoutingTable, 'get_best_route_for_destination', return_value={'next_node': '0204'}), \
                patch.object(protocol_lite.ProtocolLite, 'send_header') as send_header_mocked:
            self.protocol.process_connect_request_header(connect_request_header_obj)
            send_header_mocked.assert_called_with('|0200|7|4|0202|0204|test1|test2|2|')

    def test_process_connect_request_header_forwarding_bad_no_route_found(self):
        variables.MY_ADDRESS = '0201'
        connect_request_header_obj = ConnectRequestHeader('0200', '0200', 5, '0202', '0201', 'test1', 'test2', '2')
        with patch.object(RoutingTable, 'get_best_route_for_destination', return_value={}), \
                patch.object(protocol_lite.ProtocolLite, 'send_header') as send_header_mocked:
            self.protocol.process_connect_request_header(connect_request_header_obj)
            send_header_mocked.assert_not_called()

    def test_send_connect_request_header(self):
        variables.MY_ADDRESS = '0201'
        with patch.object(RoutingTable, 'check_peer_is_already_registered', return_value=True), \
                patch.object(RoutingTable, 'check_connect_request_entry_already_exists', return_value=False), \
                patch.object(RoutingTable, 'get_address_of_peer') as get_address_of_peer_mocked, \
                patch.object(RoutingTable, 'get_best_route_for_destination', return_value={'next_node': '0202'}), \
                patch.object(protocol_lite.ProtocolLite, 'send_header') as send_header_mocked:
            get_address_of_peer_mocked.side_effect = ['0201', '0202']
            self.protocol.send_connect_request_header('Alice', 'Bob', 60)

            self.assertTrue(call('Alice') in get_address_of_peer_mocked.call_args_list)
            self.assertTrue(call('Bob') in get_address_of_peer_mocked.call_args_list)
            send_header_mocked.assert_called_with('|0201|7|5|0202|0202|Alice|Bob|60|')

    def test_send_connect_request_header_edge_no_route_in_routing_table(self):
        variables.MY_ADDRESS = '0201'
        with patch.object(RoutingTable, 'check_peer_is_already_registered', return_value=True), \
                patch.object(RoutingTable, 'check_connect_request_entry_already_exists', return_value=False), \
                patch.object(RoutingTable, 'get_address_of_peer') as get_address_of_peer_mocked, \
                patch.object(RoutingTable, 'get_best_route_for_destination') as get_best_route_mocked, \
                patch.object(protocol_lite.ProtocolLite, 'send_header') as send_header_mocked, \
                patch.object(protocol_lite.ProtocolLite, 'send_route_request_message',
                             return_value=True) as route_request:
            get_best_route_mocked.side_effect = [{}, {'next_node': '0202'}]

            get_address_of_peer_mocked.side_effect = ['0201', '0202']
            self.protocol.send_connect_request_header('Alice', 'Bob', 60)

            route_request.assert_called_with('0202')
            send_header_mocked.assert_called_with('|0201|7|5|0202|0202|Alice|Bob|60|')

    def test_send_connect_request_header_bad_no_answer_on_route_request(self):
        variables.MY_ADDRESS = '0201'
        with patch.object(RoutingTable, 'check_peer_is_already_registered', return_value=True), \
                patch.object(RoutingTable, 'check_connect_request_entry_already_exists', return_value=False), \
                patch.object(RoutingTable, 'get_address_of_peer') as get_address_of_peer_mocked, \
                patch.object(RoutingTable, 'get_best_route_for_destination', return_value={}), \
                patch.object(protocol_lite.ProtocolLite, 'send_header') as send_header_mocked, \
                patch.object(protocol_lite.ProtocolLite, 'send_route_request_message', return_value=False):
            get_address_of_peer_mocked.side_effect = ['0201', '0202']

            self.protocol.send_connect_request_header('Alice', 'Bob', 60)

            send_header_mocked.assert_not_called()

    def test_send_header_good(self):
        with patch.object(protocol_lite, 'wait_random_time') as wait_random_time_mocked:
            serial_connection.status_q.put(True)
            serial_connection.status_q.put(True)

            self.protocol.send_header('test')
            self.assertEqual(('AT+SEND=4', ['AT,OK']), serial_connection.writing_q.get())
            self.assertEqual(('test', ['AT,SENDING', 'AT,SENDED']), serial_connection.writing_q.get())
            wait_random_time_mocked.assert_called_once()

    def test_send_header_bad_access_send_mode_false(self):
        with patch.object(protocol_lite, 'wait_random_time') as wait_random_time_mocked:
            serial_connection.status_q.put(False)

            self.protocol.send_header('test')
            self.assertEqual(('AT+SEND=4', ['AT,OK']), serial_connection.writing_q.get())
            self.assertTrue(serial_connection.writing_q.empty())
            wait_random_time_mocked.assert_called_once()

    def test_process_incoming_route_request(self):
        with patch.object(RoutingTable, 'add_neighbor_to_routing_table') as add_neighbor_mocked, \
                patch.object(protocol_lite.ProtocolLite, 'process_route_request') as process_route_request_mocked:
            serial_connection.response_q.put('LR,0136,10,|0137|3|8|4|0138|')
            self.protocol.PROCESS_INCOMING_MESSAGES = MagicMock()
            self.protocol.PROCESS_INCOMING_MESSAGES.__bool__.side_effect = [True, False]
            self.protocol.process_incoming_message()
            process_route_request_mocked.assert_called_once()
            add_neighbor_mocked.assert_called_once()

    def test_process_incoming_message_header(self):
        with patch.object(RoutingTable, 'add_neighbor_to_routing_table'), \
                patch.object(protocol_lite.ProtocolLite, 'process_message_header') as process_message_header_mocked:
            serial_connection.response_q.put('LR,0136,10,|0135|1|3|0138|0137|000001|hello|')
            self.protocol.PROCESS_INCOMING_MESSAGES = MagicMock()
            self.protocol.PROCESS_INCOMING_MESSAGES.__bool__.side_effect = [True, False]
            self.protocol.process_incoming_message()
            process_message_header_mocked.assert_called_once()

    def test_process_incoming_route_reply_header(self):
        with patch.object(RoutingTable, 'add_neighbor_to_routing_table'), \
                patch.object(protocol_lite.ProtocolLite, 'process_route_reply_header') as process_route_reply_mocked:
            serial_connection.response_q.put('LR,0136,10,|0137|4|8|3|0139|0140|')
            self.protocol.PROCESS_INCOMING_MESSAGES = MagicMock()
            self.protocol.PROCESS_INCOMING_MESSAGES.__bool__.side_effect = [True, False]
            self.protocol.process_incoming_message()
            process_route_reply_mocked.assert_called_once()

    def test_process_incoming_route_error_header(self):
        with patch.object(RoutingTable, 'add_neighbor_to_routing_table'), \
                patch.object(protocol_lite.ProtocolLite, 'process_route_error_header') as process_route_error_mocked:
            serial_connection.response_q.put('LR,0131,10,|0131|5|4|0132|')
            self.protocol.PROCESS_INCOMING_MESSAGES = MagicMock()
            self.protocol.PROCESS_INCOMING_MESSAGES.__bool__.side_effect = [True, False]
            self.protocol.process_incoming_message()
            process_route_error_mocked.assert_called_once()

    def test_process_incoming_message_ack_header(self):
        with patch.object(RoutingTable, 'add_neighbor_to_routing_table'), \
                patch.object(protocol_lite.ProtocolLite, 'process_ack_header') as process_ack_header_mocked:
            serial_connection.response_q.put('LR,0137,16,|0137|2|5|0138|8774d3|')
            self.protocol.PROCESS_INCOMING_MESSAGES = MagicMock()
            self.protocol.PROCESS_INCOMING_MESSAGES.__bool__.side_effect = [True, False]
            self.protocol.process_incoming_message()
            process_ack_header_mocked.assert_called_once()

    def test_process_incoming_registration_header(self):
        with patch.object(RoutingTable, 'add_neighbor_to_routing_table'), \
                patch.object(protocol_lite.ProtocolLite, 'process_registration_header') as process_registration_mocked:
            serial_connection.response_q.put('LR,0131,10,|0131|6|4|true|test|')
            self.protocol.PROCESS_INCOMING_MESSAGES = MagicMock()
            self.protocol.PROCESS_INCOMING_MESSAGES.__bool__.side_effect = [True, False]
            self.protocol.process_incoming_message()
            process_registration_mocked.assert_called_once()

    def test_process_incoming_connect_request_header(self):
        with patch.object(RoutingTable, 'add_neighbor_to_routing_table'), \
                patch.object(protocol_lite.ProtocolLite, 'process_connect_request_header') as connect_request_mocked:
            serial_connection.response_q.put('LR,0131,10,|0131|7|4|0132|0132|alice|bob|60|')
            self.protocol.PROCESS_INCOMING_MESSAGES = MagicMock()
            self.protocol.PROCESS_INCOMING_MESSAGES.__bool__.side_effect = [True, False]
            self.protocol.process_incoming_message()
            connect_request_mocked.assert_called_once()

    def test_process_incoming_message_bad_invalid_format(self):
        with patch.object(RoutingTable, 'add_neighbor_with_unsupported_protocol') as add_unsupported_node_mocked:
            serial_connection.response_q.put('LR,0200,10,invalid message')
            self.protocol.PROCESS_INCOMING_MESSAGES = MagicMock()
            self.protocol.PROCESS_INCOMING_MESSAGES.__bool__.side_effect = [True, False]
            self.protocol.process_incoming_message()
            add_unsupported_node_mocked.assert_called_once()

    def test_process_incoming_message_bad_invalid_format_without_source_address(self):
        with patch.object(RoutingTable, 'add_neighbor_with_unsupported_protocol') as add_unsupported_node_mocked:
            serial_connection.response_q.put('invalid message')
            self.protocol.PROCESS_INCOMING_MESSAGES = MagicMock()
            self.protocol.PROCESS_INCOMING_MESSAGES.__bool__.side_effect = [True, False]
            self.protocol.process_incoming_message()
            add_unsupported_node_mocked.assert_not_called()

    def test_send_message_good(self):
        self.protocol.connected_node = 'alice'
        with patch.object(RoutingTable, 'get_best_route_for_destination',
                          return_value={'destination': '0100', 'next_node': '0101'}), \
                patch.object(protocol_lite.ProtocolLite, 'add_message_to_waiting_acknowledgement_list'), \
                patch.object(protocol_lite.ProtocolLite, 'send_header') as send_header_mocked:
            message = b'hello alice!'
            self.protocol.send_message(message)
            send_header_mocked.assert_called_with(
                f'|0130|1|5|alice|0101|000001|{base64.b64encode(message).decode("ascii")}|')

    def test_send_message_edge_no_entry_in_routing_table(self):
        self.protocol.connected_node = 'alice'
        with patch.object(RoutingTable, 'get_best_route_for_destination') as get_best_route_mocked, \
                patch.object(protocol_lite.ProtocolLite, 'add_message_to_waiting_acknowledgement_list'), \
                patch.object(protocol_lite.ProtocolLite, 'send_route_request_message') as send_route_request_mocked, \
                patch.object(protocol_lite.ProtocolLite, 'send_header') as send_header_mocked:
            message = b'hello alice!'
            get_best_route_mocked.side_effect = [{}, {'destination': '0100', 'next_node': '0101'}]
            self.protocol.send_message(message)
            send_header_mocked.assert_called_with(
                f'|0130|1|5|alice|0101|000001|{base64.b64encode(message).decode("ascii")}|')
            send_route_request_mocked.assert_called_once()

    def test_send_message_bad_no_route_found(self):
        self.protocol.connected_node = 'alice'
        with patch.object(RoutingTable, 'get_best_route_for_destination', return_value={}), \
                patch.object(protocol_lite.ProtocolLite, 'add_message_to_waiting_acknowledgement_list'), \
                patch.object(protocol_lite.ProtocolLite, 'send_route_request_message',
                             return_value=False) as send_route_request_mocked, \
                patch.object(protocol_lite.ProtocolLite, 'send_header') as send_header_mocked:
            message = b'hello alice!'
            self.protocol.send_message(message)
            send_header_mocked.assert_not_called()
            send_route_request_mocked.assert_called_once()

    def test_send_message_bad_message_not_acknowledged(self):
        self.protocol.connected_node = 'alice'
        with patch.object(RoutingTable, 'get_best_route_for_destination',
                          return_value={'destination': '0100', 'next_node': '0101'}), \
                patch.object(protocol_lite.ProtocolLite, 'send_header') as send_header_mocked, \
                patch.object(time, 'sleep'):
            message = b'hello alice!'
            self.protocol.send_message(message)
            # verify route error was sent
            send_header_mocked.assert_called_with('|0130|5|5|alice|')

    def test_send_route_request_message_good(self):
        with patch.object(RoutingTable, 'get_best_route_for_destination',
                          return_value={'destination': '0100', 'next_node': '0101'}), \
                patch.object(protocol_lite.ProtocolLite, 'send_header') as send_header_mocked:
            self.assertTrue(self.protocol.send_route_request_message('0100'))
            # verify route request was sent
            send_header_mocked.assert_called_with('|0130|3|5|0|0100|')

    def test_send_route_request_message_bad_no_answer(self):
        with patch.object(RoutingTable, 'get_best_route_for_destination', return_value={}), \
                patch.object(protocol_lite.ProtocolLite, 'send_header') as send_header_mocked, \
                patch.object(time, 'sleep'):
            self.assertFalse(self.protocol.send_route_request_message('0100'))
            # verify route request was sent
            send_header_mocked.assert_called_with('|0130|3|5|0|0100|')

    def test_process_route_request_good(self):
        with patch.object(protocol_lite.ProtocolLite, 'send_route_reply') as send_route_reply_mocked:
            route_request_header_obj = header.RouteRequestHeader('0131', '0130', 9, 1, '0133')
            variables.MY_ADDRESS = '0133'
            self.protocol.process_route_request(route_request_header_obj)
            send_route_reply_mocked.assert_called_once()

    def test_process_route_request_good_forwarding(self):
        with patch.object(protocol_lite.ProtocolLite, 'send_header') as send_header_mocked:
            route_request_header_obj = header.RouteRequestHeader('0132', '0131', 9, 1, '0133')
            variables.MY_ADDRESS = '0134'
            self.protocol.process_route_request(route_request_header_obj)
            send_header_mocked.assert_called_with('|0131|3|8|2|0133|')

    def test_process_route_request_bad_already_forwarded(self):
        with patch.object(protocol_lite.ProtocolLite, 'send_header') as send_header_mocked, \
                patch.object(RoutingTable, 'check_route_request_already_processed', return_value=True):
            route_request_header_obj = header.RouteRequestHeader('0132', '0131', 9, 1, '0133')
            variables.MY_ADDRESS = '0134'
            self.protocol.process_route_request(route_request_header_obj)
            send_header_mocked.assert_not_called()

    def test_send_route_reply_header(self):
        with patch.object(protocol_lite.ProtocolLite, 'send_header') as send_header_mocked:
            self.protocol.send_route_reply('0131', '0132')
            send_header_mocked.assert_called_with('|0130|4|5|0|0132|0131|')

    def test_process_message_header_good(self):
        with patch.object(protocol_lite.ProtocolLite, 'send_header') as send_header_mocked:
            variables.MY_ADDRESS = '0134'
            self.protocol.connected_node = '0130'
            message_header_obj = header.MessageHeader('0131', '0130', 9, '0134', '0132', 1, base64.b64encode(b'hello'))
            self.protocol.process_message_header(message_header_obj)
            send_header_mocked.assert_called_with('|0134|2|5|0130|1|')

    def test_process_message_header_good_forward_request(self):
        with patch.object(protocol_lite.ProtocolLite, 'send_header') as send_header_mocked, \
                patch.object(RoutingTable, 'get_best_route_for_destination',
                             return_value={'destination': '0132', 'next_node': '0133'}):
            variables.MY_ADDRESS = '0134'
            message_base64_encoded = base64.b64encode(b'hello')
            message_header_obj = header.MessageHeader('0131', '0130', 9, '0132', '0134', 1, message_base64_encoded)
            self.protocol.process_message_header(message_header_obj)
            send_header_mocked.assert_called_with(f'|0130|1|8|0132|0133|000001|{message_base64_encoded}|')
