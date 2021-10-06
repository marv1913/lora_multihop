import base64
import hashlib
import logging
import random
import signal
import threading
import time
import traceback
from queue import Queue
from contextlib import contextmanager

from lora_multihop import ipc, serial_connection, header, variables
from lora_multihop.header import RegistrationHeader, ConnectRequestHeader, DisconnectRequestHeader
from lora_multihop.routing_table import RoutingTable

__author__ = "Marvin Rausch"


class ProtocolLite:
    PROCESS_INCOMING_MESSAGES = True
    VERIFICATION_TIMEOUT = 25
    PAUSE_PROCESSING_INCOMING_MESSAGES = False
    MESSAGES_ACKNOWLEDGMENT = []

    def __init__(self):
        logging.info('created protocol obj: {}'.format(str(self)))
        self.routing_table = RoutingTable()
        self.received_messages_queue = Queue()
        self.sending_messages_queue = Queue()
        self.sending_queue = Queue()

        self.connected_node = None
        self.message_counter = 0
        self.received_own_registration_message = False

    def start_protocol_thread(self):
        """
        starts new thread which processes incoming messages in background
        """
        receiving_thread = threading.Thread(target=self.process_incoming_message)
        receiving_thread.start()

    def send_header(self, header_str):
        """
        sends a string to LoRa network
        @param header_str: message to send
        """
        wait_random_time()
        serial_connection.writing_q.put(('AT+SEND={}'.format(str(len(header_str))), ['AT,OK']))
        if serial_connection.status_q.get(timeout=self.VERIFICATION_TIMEOUT):
            serial_connection.writing_q.put((header_str, ['AT,SENDING', 'AT,SENDED']))
            if serial_connection.status_q.get(timeout=self.VERIFICATION_TIMEOUT):
                logging.debug("sent header '{}'.".format(header_str))
                return
        logging.debug("could not send header '{}', because got invalid status from lora module".format(header_str))

    def process_incoming_message(self):
        """
        get messages from LoRa module, create header object and call appropriate method to process the received message
        """
        while self.PROCESS_INCOMING_MESSAGES:
            if not serial_connection.response_q.empty() and not self.PAUSE_PROCESSING_INCOMING_MESSAGES:
                raw_message = serial_connection.response_q.get()
                logging.debug(f'process: {raw_message}')
                try:
                    header_obj = header.create_header_obj_from_raw_message(raw_message)
                    if header_obj.ttl > 1:
                        self.routing_table.add_neighbor_to_routing_table(header_obj)
                        if header_obj.flag == header.RouteRequestHeader.HEADER_TYPE:
                            self.process_route_request(header_obj)
                        elif header_obj.flag == header.MessageHeader.HEADER_TYPE:
                            self.process_message_header(header_obj)
                        elif header_obj.flag == header.RouteReplyHeader.HEADER_TYPE:
                            self.process_route_reply_header(header_obj)
                        elif header_obj.flag == header.RouteErrorHeader.HEADER_TYPE:
                            self.process_route_error_header(header_obj)
                        elif header_obj.flag == header.MessageAcknowledgeHeader.HEADER_TYPE:
                            self.process_ack_header(header_obj)
                        elif header_obj.flag == header.RegistrationHeader.HEADER_TYPE:
                            self.process_registration_header(header_obj)
                        elif header_obj.flag == header.ConnectRequestHeader.HEADER_TYPE:
                            self.process_connect_request_header(header_obj)
                        elif header_obj.flag == header.DisconnectRequestHeader.HEADER_TYPE:
                            self.process_disconnect_request_header(header_obj)
                except ValueError as e:
                    logging.warning(str(e))
                    traceback.print_exc()
                    try:
                        logging.debug('try to add received signal to unsupported devices list...')
                        addr = header.get_received_from_value(raw_message)
                        self.routing_table.add_neighbor_with_unsupported_protocol(addr)
                    except ValueError as e:
                        logging.warning(str(e))

    def send_message(self, payload):
        """
        send message to currently connected peer
        @param payload: message to send as bytes
        """
        if self.connected_node is not None:
            destination = self.connected_node
            best_route = self.routing_table.get_best_route_for_destination(destination)
            if len(best_route) == 0:
                logging.info('could not find a route to {}. Sending route request...'.format(destination))
                if self.send_route_request_message(destination):
                    best_route = self.routing_table.get_best_route_for_destination(destination)
                else:
                    logging.info('Got no answer on route requested.'.format(destination))
                    return
            self.message_counter += 1
            header_obj = header.MessageHeader(None, variables.MY_ADDRESS, variables.DEFAULT_TTL, destination,
                                              best_route['next_node'], self.message_counter,
                                              base64.b64encode(payload).decode(variables.ENCODING))
            attempt = 0
            self.add_message_to_waiting_acknowledgement_list(header_obj)
            message_confirmed = False
            while attempt < 3 and not message_confirmed:
                logging.debug(f'attempt: {attempt}')
                self.send_header(header_obj.get_header_str())
                attempt_count_received_ack = 0
                while attempt_count_received_ack < 10:
                    if header_obj.message_id not in self.MESSAGES_ACKNOWLEDGMENT:
                        message_confirmed = True
                        break
                    else:
                        time.sleep(0.5)
                        attempt_count_received_ack += 1
                if message_confirmed:
                    break
                else:
                    attempt += 1
            if message_confirmed:
                print('*******************message was acknowledged by receiver*******************')
            else:
                logging.debug(
                    f'message was not acknowledged by receiver. Current ack_list: {self.MESSAGES_ACKNOWLEDGMENT}'
                    f'\nSending route error message')
                self.routing_table.delete_all_entries_of_destination(destination)
                self.delete_from_ack_list(header_obj.message_id)
                self.send_header(header.RouteErrorHeader(None, variables.MY_ADDRESS, variables.DEFAULT_TTL,
                                                         header_obj.destination).get_header_str())

    def send_route_request_message(self, end_node):
        """
        sends route request
        @param end_node: node for which a route is required
        @return: True, if route request was confirmed, else False
        """
        route_request_header_obj = header.RouteRequestHeader(None, variables.MY_ADDRESS, variables.DEFAULT_TTL, 0,
                                                             end_node)
        attempt = 0
        message_confirmed = False
        while attempt < 3 and not message_confirmed:
            logging.debug('attempt: {}'.format(attempt))
            self.send_header(route_request_header_obj.get_header_str())
            check_request_attempt_count = 0
            while check_request_attempt_count < 10:
                if len(self.routing_table.get_best_route_for_destination(end_node)) != 0:
                    logging.debug('new route for {} found'.format(end_node))
                    message_confirmed = True
                    break
                else:
                    time.sleep(0.5)
                    check_request_attempt_count += 1
            attempt += 1
            if message_confirmed:
                return message_confirmed
            else:
                attempt += 1
        return message_confirmed

    def process_route_request(self, header_obj):
        """
        processes received route request header
        @param header_obj: route request header object
        """
        # first of all check whether source of route request is myself (to prevent cycle)
        if header_obj.source != variables.MY_ADDRESS:
            # look whether requested node is myself
            if header_obj.end_node == variables.MY_ADDRESS:
                logging.debug('add new routing table entry before sending route reply')
                self.routing_table.add_routing_table_entry(header_obj.source, header_obj.received_from,
                                                           header_obj.hops + 1)
                logging.info('sending route reply message...')
                self.send_route_reply(next_node=header_obj.received_from, end_node=header_obj.source)
            else:
                if len(self.routing_table.get_best_route_for_destination(header_obj.source)) == 0:
                    # if there is no entry for source of route request, you can add routing table entry
                    self.routing_table.add_routing_table_entry(header_obj.source, header_obj.received_from,
                                                               header_obj.hops)

                header_obj.ttl = header_obj.ttl - 1
                header_obj.hops = header_obj.hops + 1
                if not self.routing_table.check_route_request_already_processed(header_obj.end_node):
                    logging.debug('forward route request message')
                    self.routing_table.add_address_to_processed_requests_list(header_obj.end_node)
                    self.send_header(header_obj.get_header_str())
                else:
                    logging.debug('route request was already processed')

    def send_route_reply(self, next_node, end_node):
        """
        sends route reply message
        @param next_node: next receiver of the message, which should forward the message to the destination node
        @param end_node: node which sent the route request
        """
        route_reply_header_obj = header.RouteReplyHeader(None, variables.MY_ADDRESS, variables.DEFAULT_TTL, 0, end_node,
                                                         next_node)
        self.send_header(route_reply_header_obj.get_header_str())

    def process_message_header(self, header_obj):
        """
        processed received message header; if the end node of the message is this node the message will be put
        into the received_messages queue to forward the message via IPC to the Java side; else the message will be
        forwarded to the next_node
        @param header_obj: message header object
        """
        if header_obj.destination == variables.MY_ADDRESS and header_obj.source == self.connected_node:
            ack_header_str = header.MessageAcknowledgeHeader(None, variables.MY_ADDRESS, variables.TTL_START_VALUE,
                                                             header_obj.source, header_obj.message_id).get_header_str()
            if self.routing_table.check_message_already_received(header_obj.source, header_obj.message_id):
                self.send_header(ack_header_str)
            else:
                logging.debug(f'payload: {str(header_obj.payload)}')
                self.received_messages_queue.put(base64.b64decode(header_obj.payload))
                # send acknowledge message
                logging.debug('sending acknowledgement')
                self.send_header(ack_header_str)

        elif header_obj.next_node == variables.MY_ADDRESS and header_obj.destination != variables.MY_ADDRESS:
            best_route = self.routing_table.get_best_route_for_destination(header_obj.destination)
            if len(best_route) == 0:
                logging.info('no routing table entry for {} to forward message found'.format(header_obj.next_node))
            else:
                header_obj.next_node = best_route['next_node']
                logging.info('forwarding message from {source} to {destination} over hop {next_node}'.format(
                    source=header_obj.source, destination=header_obj.destination, next_node=header_obj.next_node))
                header_obj.ttl = header_obj.ttl - 1
                self.send_header(header_obj.get_header_str())
        else:
            logging.debug('ignoring message: {}'.format(str(header_obj)))

    def process_route_reply_header(self, header_obj):
        """
        processes route reply header; if the source address is equal to the own address the message will be rejected;
        if the destination address is equal to the own address a new route will be added to the routing table, else
        the message will be forwarded to the address mentioned in the next_node field
        @param header_obj: route reply header object
        """
        if header_obj.source == variables.MY_ADDRESS:
            return
        if header_obj.end_node == variables.MY_ADDRESS:
            # add entry to routing table
            self.routing_table.add_routing_table_entry(header_obj.source, header_obj.received_from, header_obj.hops + 1)
        elif header_obj.next_node == variables.MY_ADDRESS:
            if len(self.routing_table.get_best_route_for_destination(header_obj.source)) != 0:
                # forward route reply message
                # add routing table entry
                logging.debug("add routing table entry before forwarding route reply message")
                self.routing_table.add_routing_table_entry(header_obj.source, header_obj.received_from,
                                                           header_obj.hops + 1)
                # forward message
                header_obj.next_node = self.routing_table.get_best_route_for_destination(header_obj.end_node)[
                    'next_node']
                header_obj.hops = header_obj.hops + 1
                header_obj.ttl = header_obj.ttl - 1
                self.send_header(header_obj.get_header_str())
            else:
                # send route error, because there is no route to forward route reply message to
                # source node of route request
                logging.info(
                    'can not forward route reply message, because there is no route to forward route reply message to')
                # source node of route request')
                # self.send_route_error(header_obj.source)

    def process_route_error_header(self, header_obj):
        """
        processes route error header; node will be deleted from routing table
        @param header_obj: route error header object
        """
        if header_obj.broken_node in self.routing_table.get_list_of_all_available_destinations():
            logging.debug(f'received route error. Remove {header_obj.broken_node} from routing table')
            self.routing_table.delete_all_entries_of_destination(header_obj.broken_node)
        else:
            logging.debug(
                f'broken node is not in available nodes: {self.routing_table.get_list_of_all_available_destinations()}')
        header_obj.ttl -= 1
        self.send_header(header_obj.get_header_str())

    def process_ack_header(self, header_obj):
        """
        processes message acknowledgement header; if the destination address is equal to the own address the header
        object will be added to the message_acknowledgement_list, else the message will be forwarded
        @param header_obj: message acknowledgement header object
        """
        if header_obj.destination == variables.MY_ADDRESS:
            self.edit_message_acknowledgment_list(header_obj)
        header_obj.ttl -= 1
        logging.debug('forward ack message')
        if header_obj.destination != variables.MY_ADDRESS:
            self.send_header(header_obj.get_header_str())
        else:
            logging.debug(f'do not forward ack message, because end node was my address')

    def process_registration_header(self, header_obj):
        if header_obj.source != variables.MY_ADDRESS:
            header_obj.ttl -= 1
            # TODO check whether this code could be used
            # if self.routing_table.check_registration_message_already_processed(header_obj.source):
            #     logging.debug('registration message already has been processed')
            # else:
            self.routing_table.add_address_to_processed_registration_messages_list(header_obj.source)
            if header_obj.subscribe:
                logging.debug('registered new peer')
                self.routing_table.add_peer(header_obj.peer_id, header_obj.source)
            else:
                logging.debug('unregistered peer')
                self.routing_table.delete_peer(header_obj.peer_id, header_obj.source)
            logging.debug('forward registration message')
            self.send_header(header_obj.get_header_str())
        else:
            self.received_own_registration_message = True

    def process_connect_request_header(self, header_obj):
        # TODO make sure same request is not forwarded multiple times
        if header_obj.received_from != variables.MY_ADDRESS:
            if header_obj.end_node == variables.MY_ADDRESS:
                self.connected_node = header_obj.source
                # send connect request to java side
                logging.debug("send connect request to java side")
                self.sending_queue.put(
                    ipc.create_connect_request_message(header_obj.source_peer_id, header_obj.target_peer_id,
                                                       header_obj.timeout))
            elif header_obj.next_node == variables.MY_ADDRESS:
                logging.debug('forward connect request header')
                route = self.routing_table.get_best_route_for_destination(header_obj.end_node)
                if len(route) > 0:
                    header_obj.next_node = route['next_node']
                    header_obj.ttl -= 1
                    self.send_header(header_obj.get_header_str())
                else:
                    logging.debug(f'could not forward connect request header, because there is no routing table entry '
                                  f'for destination address {header_obj.end_node}')

    def process_disconnect_request_header(self, header_obj):
        # TODO make sure same request is not forwarded multiple times
        if header_obj.received_from != variables.MY_ADDRESS:
            if header_obj.end_node == variables.MY_ADDRESS:
                self.connected_node = header_obj.source
                # send connect request to java side
                logging.debug("send disconnect request to java side")
                self.sending_queue.put(
                    ipc.create_disconnect_request_message(header_obj.source_peer_id, header_obj.target_peer_id))
            elif header_obj.next_node == variables.MY_ADDRESS:
                logging.debug('forward disconnect request header')
                route = self.routing_table.get_best_route_for_destination(header_obj.end_node)
                if len(route) > 0:
                    header_obj.next_node = route['next_node']
                    header_obj.ttl -= 1
                    self.send_header(header_obj.get_header_str())
                else:
                    logging.debug(f'could not forward connect request header, because there is no routing table entry '
                                  f'for destination address {header_obj.end_node}')

    def send_connect_request_header(self, source_peer_id, target_peer_id, timeout_in_sec):
        # look for address of source peer id and check whether source peer is already registered
        # wait until timeout for ConnectRequestHeader of other HubConnector
        self.check_peers(source_peer_id, target_peer_id)
        if not self.routing_table.check_connect_request_entry_already_exists(source_peer_id, target_peer_id):
            self.routing_table.add_connect_request(source_peer_id, target_peer_id)
            end_node = self.routing_table.get_address_of_peer(target_peer_id)
            route = self.routing_table.get_best_route_for_destination(end_node)
            if len(route) == 0:
                logging.info(
                    'could not find a route to {}. Sending route request...'.format(end_node))
                if self.send_route_request_message(end_node):
                    route = self.routing_table.get_best_route_for_destination(end_node)
                else:
                    logging.info('Got no answer on route requested.'.format(end_node))
                    return
            self.send_header(ConnectRequestHeader(None, variables.MY_ADDRESS, variables.DEFAULT_TTL, end_node,
                                                  route['next_node'], source_peer_id, target_peer_id,
                                                  timeout_in_sec).get_header_str())

    def send_disconnect_request_header(self, source_peer_id, target_peer_id):
        # look for address of source peer id and check whether source peer is already registered
        # TODO wait until timeout for ConnectRequestHeader of other HubConnector
        self.check_peers(source_peer_id, target_peer_id)
        end_node = self.routing_table.get_address_of_peer(target_peer_id)
        route = self.routing_table.get_best_route_for_destination(end_node)
        if len(route) == 0:
            logging.info(f'could not find a route to {end_node}. Sending route request...')
            if self.send_route_request_message(end_node):
                route = self.routing_table.get_best_route_for_destination(end_node)
            else:
                logging.info(f'Got no answer on route requested for end node: {end_node}')
                return
        self.send_header(DisconnectRequestHeader(None, variables.MY_ADDRESS, variables.DEFAULT_TTL, end_node,
                                                 route['next_node'], source_peer_id, target_peer_id).get_header_str())

    def check_peers(self, source_peer_id, target_peer_id):
        if not self.routing_table.check_peer_is_already_registered(source_peer_id):
            raise ValueError(f"source peer '{source_peer_id}' is not registered")
        elif not self.routing_table.check_peer_is_already_registered(target_peer_id):
            raise ValueError(f"target peer '{target_peer_id}' is not registered")
        elif self.routing_table.get_address_of_peer(source_peer_id) != variables.MY_ADDRESS:
            # TODO is source_peer always registered on own instance?
            raise ValueError('source peer is not registered on this node')

    def send_registration_message(self, subscribe, peer_id):
        if subscribe:
            self.routing_table.add_peer(peer_id, variables.MY_ADDRESS)
        else:
            self.routing_table.delete_peer(peer_id, variables.MY_ADDRESS)
        attempts = 0
        received_own_request = False
        self.received_own_registration_message = False

        while attempts < 3:
            self.send_header(RegistrationHeader(None, variables.MY_ADDRESS, variables.DEFAULT_TTL, subscribe,
                                                peer_id).get_header_str())
            check_attempt_count = 0
            while check_attempt_count < 5:
                if self.received_own_registration_message:
                    received_own_request = True
                    break
                else:
                    check_attempt_count += 1
                    time.sleep(0.5)
            attempts += 1
            if received_own_request:
                return

    def send_route_error(self, end_node):
        route_error_header_obj = header.RouteErrorHeader(None, variables.MY_ADDRESS, 9, end_node)
        self.send_header(route_error_header_obj.get_header_str())

    def send_message_acknowledgement(self, source, destination, payload):
        ack_header_obj = header.MessageAcknowledgeHeader(None, destination, 9, calculate_ack_id(source, payload))
        self.send_header(ack_header_obj.get_header_str())

    def stop(self):
        self.PROCESS_INCOMING_MESSAGES = False
        serial_connection.CONSUMER_THREAD_ACTIVE = False
        serial_connection.PRODUCER_THREAD_ACTIVE = False

    def add_message_to_waiting_acknowledgement_list(self, message_header_obj):
        message_id = message_header_obj.message_id
        logging.debug(f"adding '{message_id}' to ack list")
        self.MESSAGES_ACKNOWLEDGMENT.append(message_id)
        return

    def edit_message_acknowledgment_list(self, message_ack_header_obj):
        self.delete_from_ack_list(message_ack_header_obj.message_id)

    def delete_from_ack_list(self, ack_id):
        logging.debug(f'remove {ack_id} from ack list')
        try:
            self.MESSAGES_ACKNOWLEDGMENT.remove(int(ack_id))
        except ValueError:
            logging.debug(f'ack is not in list. Current ack list: {self.MESSAGES_ACKNOWLEDGMENT}')


@contextmanager
def timeout(time_in_sec):
    # Register a function to raise a TimeoutError on the signal.
    signal.signal(signal.SIGALRM, raise_timeout)
    # Schedule the signal to be sent after ``time``.
    signal.alarm(time_in_sec)
    try:
        yield
    except TimeoutError:
        pass
    finally:
        # Unregister the signal so it won't be triggered
        # if the timeout is not reached.
        signal.signal(signal.SIGALRM, signal.SIG_IGN)


def raise_timeout(signum, frame):
    raise TimeoutError


def wait_random_time():
    sleep_time = random.uniform(0, variables.MAX_SLEEP_TIME)
    logging.debug('waiting {} seconds before sending'.format(sleep_time))
    time.sleep(sleep_time)


def calculate_ack_id(address, payload):
    hash_object = hashlib.md5(bytes(address + payload, variables.ENCODING))
    return hash_object.hexdigest()[:6]

