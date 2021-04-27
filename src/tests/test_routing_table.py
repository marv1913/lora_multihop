import unittest

__author__ = "Marvin Rausch"

from protocol.routing_table import RoutingTable


class RoutingTableTest(unittest.TestCase):

    def setUp(self):
        self.routing_table = RoutingTable()

    def test_get_best_route_for_destination_good(self):
        self.routing_table.add_routing_table_entry('0136', '0138', 2)
        self.routing_table.add_routing_table_entry('0136', '0136', 0)
        self.routing_table.add_routing_table_entry('0136', '0137', 1)
        self.assertEqual({'destination': '0136', 'next_node': '0136', 'hops': 0}, self.routing_table.get_best_route_for_destination('0136'))

    def test_get_best_route_for_destination_edge_no_route_found(self):
        self.assertEqual(0, len(self.routing_table.get_best_route_for_destination('0136')))

    def test_route_request_already_processed_good1(self):
        self.routing_table.add_address_to_processed_requests_list('0131')
        self.assertTrue(self.routing_table.check_route_request_already_processed('0131'))

    def test_route_request_already_processed_good2(self):
        self.routing_table.add_address_to_processed_requests_list('0131')
        self.assertFalse(self.routing_table.check_route_request_already_processed('0132'))

    def test_registration_message_already_processed_good1(self):
        self.routing_table.add_address_to_processed_registration_messages_list('0131')
        self.assertTrue(self.routing_table.check_registration_message_already_processed('0131'))

    def test_route_request_already_processed_good2(self):
        self.routing_table.add_address_to_processed_registration_messages_list('0131')
        self.assertFalse(self.routing_table.check_registration_message_already_processed('0132'))

