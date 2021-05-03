import unittest
from unittest.mock import patch

from protocol import protocol_lite, header
from protocol.header import RegistrationHeader, ConnectRequestHeader
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

    def test_process_registration_message_header_edge_same_message_two_times(self):
        registration_message_header_obj = RegistrationHeader(None, '0131', 0, True, 'testPeer')
        with patch.object(protocol_lite.ProtocolLite, 'send_header') as send_header_mocked:
            self.protocol.process_registration_header(registration_message_header_obj)
            self.protocol.process_registration_header(registration_message_header_obj)

            self.assertEqual(1, send_header_mocked.call_count)

    def test_process_registration_message_header_bad_own_message(self):
        registration_message_header_obj = RegistrationHeader(None, '0130', 0, True, 'testPeer')
        with patch.object(protocol_lite.ProtocolLite, 'send_header') as send_header_mocked:
            self.protocol.process_registration_header(registration_message_header_obj)

            self.assertEqual(0, send_header_mocked.call_count)

    def test_process_connect_request_header_good(self):
        variables.MY_ADDRESS = '0201'
        connect_request_header_obj = ConnectRequestHeader('0200', '0200', 5, '0201', '0201', 'test1', 'test2')
        self.protocol.process_connect_request_header(connect_request_header_obj)
