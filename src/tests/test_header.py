import unittest

from protocol import header

__author__ = "Marvin Rausch"


class HeaderTest(unittest.TestCase):

    def test_create_route_request_header_obj_good(self):
        header_obj = header.create_header_obj_from_raw_message('LR,0136,10,|0137|3|8|4|0138|')
        self.assertEqual(header_obj.source, '0137')
        self.assertEqual(header_obj.flag, 3)
        self.assertEqual(header_obj.ttl, 8)
        self.assertEqual(header_obj.end_node, '0138')
        self.assertEqual(header_obj.hops, 4)

    def test_create_route_request_header_obj_bad_hops_missing(self):
        self.assertRaises(ValueError, header.create_header_obj_from_raw_message, 'LR,0136,10,|0137|3|8|0138|')

    def test_create_route_request_header_bad_to_many_args(self):
        self.assertRaises(ValueError, header.create_header_obj_from_raw_message, 'LR,0136,10,|0137|3|8|4|0138|0|')

    def test_create_route_reply_header_obj_good(self):
        header_obj = header.create_header_obj_from_raw_message('LR,0136,10,|0137|4|8|3|0139|0140|')
        self.assertEqual(header_obj.source, '0137')
        self.assertEqual(header_obj.received_from, '0136')
        self.assertEqual(header_obj.end_node, '0139')
        self.assertEqual(header_obj.next_node, '0140')
        self.assertEqual(header_obj.flag, 4)
        self.assertEqual(header_obj.ttl, 8)
        self.assertEqual(header_obj.hops, 3)

    def test_create_message_ack_header_good(self):
        header_obj = header.create_header_obj_from_raw_message('LR,0137,16,|0137|2|5|0138|8774d3|')
        self.assertEqual(header_obj.flag, 2)

    def test_create_route_reply_header_obj_bad_invalid_flag(self):
        self.assertRaises(ValueError, header.create_header_obj_from_raw_message, 'LR,0136,10,|0137|8|8|3|0139|0140|')

    def test_create_message_header_obj_good(self):
        header_obj = header.create_header_obj_from_raw_message('LR,0136,10,|0135|1|3|0138|0137|hello|')
        self.assertEqual(header_obj.source, '0135')
        self.assertEqual(header_obj.destination, '0138')
        self.assertEqual(header_obj.flag, 1)
        self.assertEqual(header_obj.ttl, 3)
        self.assertEqual(header_obj.next_node, '0137')
        self.assertEqual(header_obj.payload, 'hello')
        self.assertEqual(header_obj.received_from, '0136')

    def test_create_message_header_obj_edge_comma_in_message(self):
        header_obj = header.create_header_obj_from_raw_message('LR,0136,10,|0135|1|3|0138|0137|hello, good morning|')
        self.assertEqual(header_obj.source, '0135')
        self.assertEqual(header_obj.destination, '0138')
        self.assertEqual(header_obj.flag, 1)
        self.assertEqual(header_obj.ttl, 3)
        self.assertEqual(header_obj.next_node, '0137')
        self.assertEqual(header_obj.payload, 'hello, good morning')
        self.assertEqual(header_obj.received_from, '0136')

    def test_create_message_header_obj_bad_payload_missing(self):
        self.assertRaises(ValueError, header.create_header_obj_from_raw_message, 'LR,0136,10,|0135|1|1|0138|0137|')

    def test_create_header_obj_bad_message_without_header(self):
        self.assertRaises(ValueError, header.create_header_obj_from_raw_message, 'LR,FFFF,0A,hello')

    def test_get_header_str_route_request_header_good(self):
        route_request_header_obj = header.RouteRequestHeader('0131', '0130', 9, 1, '0133')
        self.assertEqual('|0130|3|9|1|0133|', route_request_header_obj.get_header_str())

    def test_get_header_str_route_reply_header_good(self):
        route_reply_header_obj = header.RouteReplyHeader('0131', '0130', 9, 1, '0132', '0133')
        self.assertEqual('|0130|4|9|1|0132|0133|', route_reply_header_obj.get_header_str())

    def test_get_header_str_message_header_good(self):
        message_header_obj = header.MessageHeader('0131', '0130', 9, '0133', '0132', 'hello')
        self.assertEqual('|0130|1|9|0133|0132|hello|', message_header_obj.get_header_str())

    def test_get_header_str_ack_header_good(self):
        message_header_obj = header.MessageAcknowledgeHeader(received_from=None, ttl=9, source='0132',
                                                             destination='0133', ack_id='example_hash')
        self.assertEqual('|0132|2|9|0133|example_hash|', message_header_obj.get_header_str())

    def test_create_header_str_route_error_header_good(self):
        route_error_header_obj = header.RouteErrorHeader('0131', '0131', 5, '0132')
        self.assertEqual('|0131|5|5|0132|', route_error_header_obj.get_header_str())

    def test_create_route_error_header_from_message_str(self):
        route_error_header_obj = header.create_header_obj_from_raw_message('LR,0131,10,|0131|5|4|0132|')

        self.assertEqual(route_error_header_obj.source, '0131')
        self.assertEqual(route_error_header_obj.ttl, 4)
        self.assertEqual(route_error_header_obj.broken_node, '0132')
        self.assertEqual(route_error_header_obj.flag, header.RouteErrorHeader.HEADER_TYPE)
