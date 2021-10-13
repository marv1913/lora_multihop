import copy
import logging
import time

from lora_multihop import variables

__author__ = "Marvin Rausch"


class RoutingTable:

    def __init__(self):
        self.routing_table = []
        self.unsupported_devices = []
        self.processed_route_requests = []
        self.processed_registration_messages = []
        self.available_peers = []
        self.received_messages = []
        self.processed_connect_request = []

    def add_routing_table_entry(self, destination, next_node, hops):
        """
        adds new entry to the routing table
        :param destination: destination address
        :param next_node: address next node
        :param hops: costs
        """
        new_routing_table_entry = {'destination': destination, 'next_node': next_node, 'hops': hops}
        if not self.check_routing_table_entry_exists(destination, next_node, hops):
            logging.debug('new entry in routing table: {}'.format(str(new_routing_table_entry)))
            self.routing_table.append(new_routing_table_entry)
            if destination in self.unsupported_devices:
                self.unsupported_devices.remove(destination)
        else:
            logging.debug('entry already exists: {}'.format(str(new_routing_table_entry)))

    def add_connect_request(self, source_peer_id, target_peer_id):
        """
        adds connect request to a list, to prevent software from processing same connect request twice
        :param source_peer_id: peer id of source peer
        :param target_peer_id: peer id of target peer
        """
        self.processed_connect_request.append(
            {'source_peer_id': source_peer_id, 'target_peer_id': target_peer_id, 'time': time.time()})

    def check_connect_request_entry_already_exists(self, source_peer_id, target_peer_id):
        """
        checks if connect request was already processed during the last 45 seconds
        :param source_peer_id: peer id of source peer
        :param target_peer_id: peer id of target peer
        :return: True if request has already been processed; else False
        """
        new_list = []
        current_time = time.time()
        for entry in self.processed_connect_request:
            if current_time - entry['time'] < 45:
                new_list.append(entry)
        for entry in new_list:
            if entry['source_peer_id'] == source_peer_id and entry['target_peer_id'] == target_peer_id:
                return True
        return False

    def check_message_already_received(self, source, message_id):
        """
        checks if MessageHeader has already been received
        :param source: source address of received message
        :param message_id: message id of received message
        :return: True if message has already been received; else False
        """
        for entry in self.received_messages:
            if entry['source'] == source and entry['message_id'] == message_id:
                return True
        return False

    def check_routing_table_entry_exists(self, destination, next_node, hops):
        """
        checks whether a route is already in routing table
        :param destination: destination address
        :param next_node: address of next node
        :param hops: costs
        :return: True if route is already saved in routing table; else False
        """
        for entry in self.routing_table:
            if entry['destination'] == destination and entry['next_node'] == next_node and entry['hops'] == hops:
                return True
        return False

    def add_neighbor_to_routing_table(self, header_obj):
        """
        adds node to routing table which is in direct range (hops==1)
        :param header_obj: object of subclass of class Header
        """
        logging.debug('call add neighbor function')
        received_from = header_obj.received_from
        self.add_routing_table_entry(received_from, received_from, 1)

    def add_neighbor_with_unsupported_protocol(self, address):
        """
        adds address to the list of nodes which send messages with another protocol
        :param address: address of node
        """
        if address not in self.unsupported_devices:
            self.unsupported_devices.append(address)

    def get_best_route_for_destination(self, destination):
        """
        method to get the route with lowest costs for given destination
        :param destination: destination address
        :return: routing table entry as dict
        """
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
        """
        method to get addresses of all available nodes in network
        :return: addresses of all available nodes as list
        """
        available_destinations = []
        for entry in self.routing_table:
            if entry['destination'] not in available_destinations:
                available_destinations.append(entry['destination'])
        return available_destinations

    def add_peer(self, peer_id, address):
        """
        adds a peer to available_peers list
        :param peer_id: id of peer
        :param address: address where peer was registered
        """
        if self.check_entry_for_peer_exists(peer_id, address):
            logging.debug('entry already exists')
        else:
            self.available_peers.append({'peer_id': peer_id, 'address': address})

    def delete_peer(self, peer_id, address):
        """
        deletes a peer from available_peers list
        :param peer_id: id of peer
        :param address: address where peer was registered
        """
        new_list = []
        for entry in self.available_peers:
            if entry['peer_id'] != peer_id and entry['address'] != address:
                new_list.append(entry)
        self.available_peers = new_list

    def get_peers(self):
        """
        method to get list of peer id's of all available peers
        :return: peer id's as list
        """
        return copy.deepcopy(self.available_peers)

    def check_entry_for_peer_exists(self, peer_id, address):
        """
        checks whether entry in available_peers list already exists
        :param peer_id: id of peer
        :param address: address where peer was registered
        :return: True if entry already exists; else False
        """
        for entry in self.available_peers:
            if entry['peer_id'] == peer_id and entry['address'] == address:
                return True
        return False

    def check_peer_is_already_registered(self, peer_id):
        """
        checks whether a peer is already registered
        :param peer_id: id of peer
        :return: True if peer already has been registered; else False
        """
        for entry in self.available_peers:
            if entry['peer_id'] == peer_id:
                return True
        return False

    def get_address_of_peer(self, peer_id):
        """
        method to get the address of the node where a peer was registered
        :param peer_id: id of peer
        :return: address where the peer was registered
        """
        for entry in self.available_peers:
            if entry['peer_id'] == peer_id:
                return entry['address']

    def add_address_to_processed_requests_list(self, address):
        """
        adds address of a received route request to a list to prevent software from forwarding same request multiple
        times (prevent cycles)
        :param address: address of destination node
        """
        self.processed_route_requests = add_address_to_processed_list(address, self.processed_route_requests)

    def add_address_to_processed_registration_messages_list(self, address):
        """
        adds address of a registration message header to a list to prevent software from processing same message
        multiple times
        :param address: source address of registration header
        """
        self.processed_registration_messages = add_address_to_processed_list(address,
                                                                             self.processed_registration_messages)

    def delete_all_entries_of_destination(self, destination):
        """
        deletes all routing table entries of a destination
        :param destination: address of destination
        """
        new_list = []
        for entry in self.routing_table:
            if destination not in entry.values():
                new_list.append(entry)
        self.routing_table = new_list

    def check_route_request_already_processed(self, address):
        """
        method to check whether a route request header already has been processed
        :param address: end node address of route request
        :return: True if request already has been processed; else False
        """
        return check_message_already_processed(address, self.processed_route_requests)


def add_address_to_processed_list(address, processed_list):
    """
    helper function which adds an address to list, to check whether message already has been processed
    :param address: address which should be added to list
    :param processed_list: list where to add the address
    :return: passed list where new item was added
    """
    processed_list = clean_already_processed_requests_list(processed_list)

    if not check_message_already_processed(address, processed_list):
        processed_list.append({'address': address, 'time': time.time()})
    return processed_list


def clean_already_processed_requests_list(processed_list):
    """
    helper function to delete all entries from list which are older than variables.PROCESSED_ROUTE_REQUEST_TIMEOUT
    :param processed_list: list where entries should be deleted
    :return: cleaned list
    """
    current_time = time.time()
    cleaned_list = []
    for address_dict in processed_list:
        if current_time - address_dict['time'] < variables.PROCESSED_ROUTE_REQUEST_TIMEOUT:
            cleaned_list.append(address_dict)
    processed_list = cleaned_list
    return processed_list


def check_message_already_processed(address, processed_list):
    """
    helper function to check whether a message already has been processed
    :param address: address to check for
    :param processed_list: list where to search for passed address
    :return: True if message already has been processed; else False
    """
    processed_list = clean_already_processed_requests_list(processed_list)

    for address_dict in processed_list:
        if address_dict['address'] == address:
            return True
    return False
