import unittest
from unittest.mock import patch

from protocol import protocol_lite, header


class ProtocolTest(unittest.TestCase):

    def setUp(self):
        self.protocol = protocol_lite.ProtocolLite()

    def test_get_best_route_for_destination_good(self):
        with patch.object(protocol_lite.ProtocolLite, 'send_header'):
            raw_message = 'LR,0133,16,|0131|2|5|0133|99fc8d|'
            header_obj = header.create_header_obj_from_raw_message(raw_message)
            self.protocol.process_ack_header(header_obj)
            self.assertEqual('|0131|2|4|0133|99fc8d|', header_obj.get_header_str())
