import unittest

__author__ = "Marvin Rausch"

from ipc import xml
from protocol.routing_table import RoutingTable


class XMLTest(unittest.TestCase):

    def setUp(self):
        self.routing_table = RoutingTable()

    def test_get_available_peers_good(self):
        self.routing_table.add_peer('test', '0131')
        self.routing_table.add_peer('test2', '0132')

        peers = self.routing_table.get_peers()
        res = xml.get_available_peers_as_xml_str(peers)
        self.assertEqual(b'<registered_peers>\n  <peer>\n    <peer_id>test</peer_id>\n  </peer>\n  <pee'
                         b'r>\n    <peer_id>test2</peer_id>\n  </peer>\n</registered_peers>\n', res)

    def test_get_available_peers_edge_empty_list(self):
        peers = self.routing_table.get_peers()
        res = xml.get_available_peers_as_xml_str(peers)
        self.assertEqual(b'<registered_peers/>\n', res)

    def test_parse_xml_good(self):
        xml_as_bytes = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<connection_request>\n' \
                       b'<source_peer_id>test201</source_peer_id>\n    <target_peer_id>test200</target_peer_id>\n' \
                       b'<timeout>45</timeout>\n</connection_request>\n '
        xml.parse_xml(xml_as_bytes)
