import unittest
from unittest.mock import patch, call

from protocol import protocol_lite, header, consumer_producer
from protocol.header import RegistrationHeader, ConnectRequestHeader
from protocol.routing_table import RoutingTable
from util import variables


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
            patch.object(protocol_lite.ProtocolLite, 'send_route_request_message', return_value=True) as route_request:
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
            consumer_producer.status_q.put(True)
            consumer_producer.status_q.put(True)

            self.protocol.send_header('test')
            self.assertEqual(('AT+SEND=4', ['AT,OK']), consumer_producer.q.get())
            self.assertEqual(('test', ['AT,SENDING', 'AT,SENDED']), consumer_producer.q.get())
            wait_random_time_mocked.assert_called_once()

    def test_send_header_bad_access_send_mode_false(self):
        with patch.object(protocol_lite, 'wait_random_time') as wait_random_time_mocked:
            consumer_producer.status_q.put(False)

            self.protocol.send_header('test')
            self.assertEqual(('AT+SEND=4', ['AT,OK']), consumer_producer.q.get())
            self.assertTrue(consumer_producer.q.empty())
            wait_random_time_mocked.assert_called_once()


