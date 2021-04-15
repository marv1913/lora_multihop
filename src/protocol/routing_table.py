import logging
import time

from util import variables

__author__ = "Marvin Rausch"


class RoutingTable:

    def __init__(self):
        self.routing_table = []
        self.unsupported_devices = []
        self.processed_route_requests = []

    def add_routing_table_entry(self, destination, next_node, hops):
        new_routing_table_entry = {'destination': destination, 'next_node': next_node, 'hops': hops}
        if not self.check_routing_table_entry_exists(destination, next_node, hops):
            logging.debug('new entry in routing table: {}'.format(str(new_routing_table_entry)))
            self.routing_table.append(new_routing_table_entry)
            if destination in self.unsupported_devices:
                self.unsupported_devices.remove(destination)
        else:
            logging.debug('entry already exists: {}'.format(str(new_routing_table_entry)))

    def check_routing_table_entry_exists(self, destination, next_node, hops):
        for entry in self.routing_table:
            if entry['destination'] == destination and entry['next_node'] == next_node and entry['hops'] == hops:
                return True
        return False

    def add_neighbor_to_routing_table(self, header_obj):
        logging.debug('call add neighbor function')
        received_from = header_obj.received_from
        self.add_routing_table_entry(received_from, received_from, 1)

    def add_neighbor_with_unsupported_protocol(self, address):
        if address not in self.unsupported_devices:
            self.unsupported_devices.append(address)

    def get_best_route_for_destination(self, destination):
        if destination not in variables.AVAILABLE_NODES:
            raise ValueError("destination address '{}' does not exist".format(destination))
        list_of_available_routes = []
        for entry in self.routing_table:
            if entry['destination'] == destination:
                list_of_available_routes.append(entry)
        best_route = {}
        if len(list_of_available_routes) != 0:
            list_of_available_routes = sorted(list_of_available_routes, key=lambda k: k['hops'])
            best_route = list_of_available_routes[0]
        return best_route

    def get_list_of_all_available_destinations(self):
        available_destinations = []
        for entry in self.routing_table:
            if entry['destination'] not in available_destinations:
                available_destinations.append(entry['destination'])
        return available_destinations

    def get_list_of_best_routes_for_all_available_destinations(self):
        best_routes = []
        for entry in self.get_list_of_all_available_destinations():
            best_route = self.get_best_route_for_destination(entry)
            if len(best_route) != 0:
                best_routes.append(best_route)
        return best_routes

    def add_address_to_processed_requests_list(self, address):
        for address_dict in self.processed_route_requests:
            if address_dict['address'] == address:
                return
        self.processed_route_requests.append({'address': address, 'time': time.time()})

    def delete_all_entries_of_destination(self, destination):
        new_list = []
        for entry in self.routing_table:
            if destination not in entry.values():
                new_list.append(entry)
        self.routing_table = new_list

    def __clean_already_processed_requests_list(self):
        current_time = time.time()
        cleaned_list = []
        for address_dict in self.processed_route_requests:
            if current_time - address_dict['time'] < variables.PROCESSED_ROUTE_REQUEST_TIMEOUT:
                cleaned_list.append(address_dict)
        self.processed_route_requests = cleaned_list

    def check_route_request_already_processed(self, address):
        self.__clean_already_processed_requests_list()
        for address_dict in self.processed_route_requests:
            if address_dict['address'] == address:
                return True
        return False
