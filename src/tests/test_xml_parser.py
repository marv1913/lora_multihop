import unittest

__author__ = "Marvin Rausch"

from ipc import xml
from protocol.routing_table import RoutingTable


class XMLTest(unittest.TestCase):

    def setUp(self):
        self.routing_table = RoutingTable()

    def test_add_peer_good(self):
        self.routing_table.add_peer('test', '0131')
        self.routing_table.add_peer('test2', '0132')

        peers = self.routing_table.get_peers()
        res = xml.get_available_peers_as_xml_str(peers)
        self.assertEqual('<registered_peers>\n  <peer>\n    <peer_id>test</peer_id>\n  </peer>\n  <peer>\n    '
            '<peer_id>test2</peer_id>\n  </peer>\n</registered_peers>\n', res)

    def test_add_peer_edge_empty_list(self):
        peers = self.routing_table.get_peers()
        res = xml.get_available_peers_as_xml_str(peers)
        self.assertEqual('<registered_peers>\n  <peer/>\n</registered_peers>', res)
