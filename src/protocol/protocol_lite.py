import hashlib
import logging
import random
import signal
import threading
import time
from contextlib import contextmanager

from protocol import consumer_producer
from protocol.header import RouteReplyHeader
from util import variables
from protocol import header
from messenger import view
from protocol.routing_table import RoutingTable

__author__ = "Marvin Rausch"


class ProtocolLite:
    PROCESS_INCOMING_MESSAGES = True
    VERIFICATION_TIMEOUT = 25
    PAUSE_PROCESSING_INCOMING_MESSAGES = False
    MESSAGES_ACKNOWLEDGMENT = []

    def __init__(self):
        logging.info('created protocol obj: {}'.format(str(self)))
        self.routing_table = RoutingTable()

    def start_protocol_thread(self):
        receiving_thread = threading.Thread(target=self.process_incoming_message)
        receiving_thread.start()

    def send_header(self, header_str):
        wait_random_time()
        consumer_producer.q.put(('AT+SEND={}'.format(str(len(header_str))), ['AT,OK']))
        if consumer_producer.status_q.get(timeout=self.VERIFICATION_TIMEOUT):
            consumer_producer.q.put((header_str, ['AT,SENDING', 'AT,SENDED']))
            if consumer_producer.status_q.get(timeout=self.VERIFICATION_TIMEOUT):
                logging.debug("header '{}' sended.".format(header_str))
                return
        logging.debug("could not send header '{}', because got invalid status from lora module".format(header_str))

    def process_incoming_message(self):
        while self.PROCESS_INCOMING_MESSAGES:
            if not consumer_producer.response_q.empty() and not self.PAUSE_PROCESSING_INCOMING_MESSAGES:
                raw_message = consumer_producer.response_q.get()

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

                except ValueError as e:
                    logging.warning(str(e))
                    try:
                        logging.debug('try to add received signal to unsupported devices list...')
                        addr = header.get_received_from_value(raw_message)
                        self.routing_table.add_neighbor_with_unsupported_protocol(addr)
                    except ValueError as e:
                        logging.warning(str(e))

    def send_message(self, destination, payload):
        best_route = self.routing_table.get_best_route_for_destination(destination)
        if len(best_route) == 0:
            logging.info(
                'could not find a route to {}. Sending route request...'.format(destination))
            if self.send_route_request_message(destination):
                best_route = self.routing_table.get_best_route_for_destination(destination)
            else:
                logging.info(
                    'Got no answer on route requested.'.format(destination))
                return
        header_obj = header.MessageHeader(None, variables.MY_ADDRESS, variables.DEFAULT_TTL, destination,
                                          best_route['next_node'], payload)
        attempt = 0
        ack_id = self.add_message_to_waiting_acknowledgement_list(header_obj)
        message_confirmed = False
        while attempt < 3 and not message_confirmed:
            logging.debug(f'attempt: {attempt}')
            self.send_header(header_obj.get_header_str())
            with timeout(5):
                try:
                    while True:
                        if ack_id not in self.MESSAGES_ACKNOWLEDGMENT:
                            message_confirmed = True
                            break
                except TimeoutError:
                    attempt = attempt + 1
        if message_confirmed:
            view.print_ack_text()
        else:
            logging.debug(f'message was not acknowledged by receiver. Current ack_list: {self.MESSAGES_ACKNOWLEDGMENT}'
                          f'\nSending route error message')
            self.routing_table.delete_all_entries_of_destination(destination)
            self.delete_from_ack_list(ack_id)
            self.send_header(header.RouteErrorHeader(None, variables.MY_ADDRESS, variables.DEFAULT_TTL,
                                                     header_obj.destination).get_header_str())

    def send_route_request_message(self, end_node):
        route_request_header_obj = header.RouteRequestHeader(None, variables.MY_ADDRESS, variables.DEFAULT_TTL, 0,
                                                             end_node)
        attempt = 0
        message_confirmed = False
        while attempt < 3 and not message_confirmed:
            self.send_header(route_request_header_obj.get_header_str())
            with timeout(5):
                try:
                    logging.debug('attempt: {}'.format(attempt))
                    while True:
                        if len(self.routing_table.get_best_route_for_destination(end_node)) != 0:
                            logging.debug('new route for {} found'.format(end_node))
                            message_confirmed = True
                            break
                except TimeoutError:
                    attempt = attempt + 1
        return message_confirmed

    def process_route_request(self, header_obj):
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
                # if len(self.routing_table.get_best_route_for_destination(header_obj.end_node)) > 0:
                #     # send route reply
                #     logging.debug(f'sending route reply to {header_obj.source} before route request is reaching '
                #                   f'destination, because found route in routing table')
                #     route = self.routing_table.get_best_route_for_destination(header_obj.end_node)
                #     route_reply = RouteReplyHeader(None, header_obj.end_node, variables.DEFAULT_TTL, route['hops'],
                #                                    header_obj.source, header_obj.received_from)
                #     self.send_header(route_reply.get_header_str())
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
        route_reply_header_obj = header.RouteReplyHeader(None, variables.MY_ADDRESS, variables.DEFAULT_TTL, 0, end_node,
                                                         next_node)
        self.send_header(route_reply_header_obj.get_header_str())

    def process_message_header(self, header_obj):
        if header_obj.destination == variables.MY_ADDRESS:
            view.display_received_message(header_obj)
            # send acknowledge message
            hash_value = calculate_ack_id(header_obj.source, header_obj.payload)
            logging.debug('sending acknowledgement')
            self.send_header(header.MessageAcknowledgeHeader(None, variables.MY_ADDRESS, variables.TTL_START_VALUE,
                                                             header_obj.source, hash_value).get_header_str())
        elif header_obj.next_node == variables.MY_ADDRESS:
            best_route = self.routing_table.get_best_route_for_destination(header_obj.destination)
            if len(best_route) == 0:
                logging.info(
                    'no routing table entry for {} to forward message found'.format(header_obj.next_node))
            else:
                header_obj.next_node = best_route['next_node']
                logging.info('forwarding message from {source} to {destination} over hop {next_node}'.format(
                    source=header_obj.source, destination=header_obj.destination, next_node=header_obj.next_node))
                header_obj.ttl = header_obj.ttl - 1
                self.send_header(header_obj.get_header_str())
        else:
            logging.debug('ignoring message: {}'.format(str(header_obj)))

    def process_route_reply_header(self, header_obj):
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
                header_obj.next_node = self.routing_table.get_best_route_for_destination(header_obj.end_node)['next_node']
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
        if header_obj.broken_node in self.routing_table.get_list_of_all_available_destinations():
            logging.debug(f'received route error. Remove {header_obj.broken_node} from routing table')
            self.routing_table.delete_all_entries_of_destination(header_obj.broken_node)
        else:
            logging.debug(
                f'broken node is not in available nodes: {self.routing_table.get_list_of_all_available_destinations()}')
        header_obj.ttl -= 1
        self.send_header(header_obj.get_header_str())

    def process_ack_header(self, header_obj):
        self.edit_message_acknowledgment_list(header_obj)
        header_obj.ttl -= 1
        logging.debug('forward ack message')
        if header_obj.destination != variables.MY_ADDRESS:
            self.send_header(header_obj.get_header_str())
        else:
            logging.debug(f'do not forward ack message, because end node was my address')

    def send_route_error(self, end_node):
        route_error_header_obj = header.RouteErrorHeader(None, variables.MY_ADDRESS, 9,
                                                         end_node)
        self.send_header(route_error_header_obj.get_header_str())

    def send_message_acknowledgement(self, source, destination, payload):
        ack_header_obj = header.MessageAcknowledgeHeader(None, destination, 9, calculate_ack_id(source, payload))
        self.send_header(ack_header_obj.get_header_str())

    def stop(self):
        self.PROCESS_INCOMING_MESSAGES = False
        consumer_producer.CONSUMER_THREAD_ACTIVE = False
        consumer_producer.PRODUCER_THREAD_ACTIVE = False

    def add_message_to_waiting_acknowledgement_list(self, message_header_obj):
        ack_id = calculate_ack_id(message_header_obj.source, message_header_obj.payload)
        logging.debug('adding {} to ack list'.format(ack_id))
        self.MESSAGES_ACKNOWLEDGMENT.append(ack_id)
        return ack_id

    def edit_message_acknowledgment_list(self, message_ack_header_obj):
        self.delete_from_ack_list(message_ack_header_obj.ack_id)

    def delete_from_ack_list(self, ack_id):
        logging.debug(f'remove {ack_id} from ack list')
        try:
            self.MESSAGES_ACKNOWLEDGMENT.remove(ack_id)
        except ValueError:
            logging.debug('ack is not in list')


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
