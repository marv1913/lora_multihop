import unittest

__author__ = "Marvin Rausch"

import time

from unittest.mock import patch

from lora_multihop import header
from lora_multihop.routing_table import RoutingTable


class RoutingTableTest(unittest.TestCase):

    def setUp(self):
        self.routing_table = RoutingTable()

    def test_get_best_route_for_destination_good(self):
        self.routing_table.add_routing_table_entry('0136', '0138', 2)
        self.routing_table.add_routing_table_entry('0136', '0136', 0)
        self.routing_table.add_routing_table_entry('0136', '0137', 1)
        self.assertEqual({'destination': '0136', 'next_node': '0136', 'hops': 0},
                         self.routing_table.get_best_route_for_destination('0136'))

    def test_get_best_route_for_destination_edge_no_route_found(self):
        self.assertEqual(0, len(self.routing_table.get_best_route_for_destination('0136')))

    def test_route_request_already_processed_good1(self):
        self.routing_table.add_address_to_processed_requests_list('0131')
        self.assertTrue(self.routing_table.check_route_request_already_processed('0131'))

    def test_route_request_already_processed_good2(self):
        self.routing_table.add_address_to_processed_requests_list('0131')
        self.assertFalse(self.routing_table.check_route_request_already_processed('0132'))

    def test_add_peer_good(self):
        self.routing_table.add_peer('test', '0131')
        self.assertEqual(1, len(self.routing_table.available_peers))

    def test_add_peer_edge_same_entry_two_times(self):
        self.routing_table.add_peer('test', '0131')
        self.routing_table.add_peer('test', '0131')
        self.assertEqual(1, len(self.routing_table.available_peers))

    def test_delete_peer_good(self):
        self.routing_table.add_peer('test', '0131')
        self.routing_table.delete_peer('test', '0131')
        self.assertEqual(0, len(self.routing_table.available_peers))

    def test_delete_peer_not_existing(self):
        self.routing_table.delete_peer('test', '0131')

    def test_check_connect_request_entry_already_exists(self):
        with patch.object(time, 'time', return_value=120):
            self.routing_table.processed_connect_request = [{'source_peer_id': '0200', 'target_peer_id': '0201',
                                                             'time': 20},
                                                            {'source_peer_id': '0201', 'target_peer_id': '0203',
                                                             'time': 100}
                                                            ]
            self.assertTrue(self.routing_table.check_connect_request_entry_already_exists('0201', '0203'))
            self.assertFalse(self.routing_table.check_connect_request_entry_already_exists('0200', '0201'))

    def test_check_message_already_received(self):
        self.routing_table.received_messages = [{'source': '0200', 'message_id': '001'}, {'source': '0201',
                                                                                          'message_id': '002'}]
        self.assertTrue(self.routing_table.check_message_already_received('0200', '001'))
        self.assertFalse(self.routing_table.check_message_already_received('0201', '001'))

    def test_add_neighbor_to_routing_table(self):
        message_header_obj = header.MessageHeader('0131', '0130', 9, '0133', '0132', 1, 'hello')
        self.routing_table.add_neighbor_to_routing_table(message_header_obj)
        self.assertTrue({'destination': '0131', 'next_node': '0131', 'hops': 1} in self.routing_table.routing_table)

    def test_get_list_of_all_available_destinations(self):
        self.routing_table.routing_table = [{'destination': '0131', 'next_node': '0131', 'hops': 1}]
        self.assertEqual(['0131'], self.routing_table.get_list_of_all_available_destinations())


    def test_get_peers(self):
        self.routing_table.add_peer('alice', '0200')
        self.assertEqual([{'address': '0200', 'peer_id': 'alice'}], self.routing_table.get_peers())

    def test_check_peer_already_registered_good(self):
        self.routing_table.add_peer('alice', '0200')
        self.assertTrue(self.routing_table.check_peer_is_already_registered('alice'))

    def test_check_peer_already_registered_bad(self):
        self.assertFalse(self.routing_table.check_peer_is_already_registered('alice'))


