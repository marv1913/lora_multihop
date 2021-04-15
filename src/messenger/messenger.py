import logging
import time

from protocol import consumer_producer
from util import variables, module_config

from prettytable import PrettyTable

from messenger import view
from protocol.protocol_lite import ProtocolLite

__author__ = "Marvin Rausch"

CONFIG_MODE = 0
SEND_MODE = 1
LIST_MODE = 2


class Messenger:
    MODE = SEND_MODE
    DESTINATION_ADDRESS = '0138'

    def __init__(self, protocol_obj):
        variables.MY_ADDRESS = consumer_producer.get_current_address_from_module()
        logging.info('loaded address of module: {}'.format(variables.MY_ADDRESS))
        self.protocol = protocol_obj
        self.protocol.start_protocol_thread()

    def start_chatting(self):
        view.print_welcome_text()
        active = True
        while active:
            text = input('>\n')
            if text == 'exit':
                active = False
                self.protocol.stop()
            elif text == 'help':
                view.print_help_text()
            elif text == ':l':
                self.print_routing_table()
            elif ':' in text:
                self.change_mode(text)
            else:
                if self.MODE == CONFIG_MODE:
                    if text == '?':
                        print('current destination address: {}'.format(self.DESTINATION_ADDRESS))
                    elif text == 'all':
                        print(variables.AVAILABLE_NODES)
                    elif text == 'config':
                        self.protocol.PAUSE_PROCESSING_INCOMING_MESSAGES = True
                        module_config.config_module()
                        # if self.module_config.config_module():
                        #     print('module successfully configured')
                        # else:
                        #     print('could not change module config')
                        time.sleep(4)
                        self.protocol.PAUSE_PROCESSING_INCOMING_MESSAGES = False
                    elif text not in variables.AVAILABLE_NODES:
                        print("address '{}' is not available".format(text))
                    else:
                        self.DESTINATION_ADDRESS = text
                        print('destination address set to: {}'.format(text))
                elif self.MODE == SEND_MODE:
                    if self.DESTINATION_ADDRESS is None:
                        print('enter config mode and set destination address before sending first message')
                    else:
                        self.protocol.send_message(self.DESTINATION_ADDRESS, text)

    def change_mode(self, text):
        if text == ':c':
            self.MODE = CONFIG_MODE
        elif text == ':s':
            self.MODE = SEND_MODE
        elif text == ':l':
            self.MODE = LIST_MODE
        else:
            print("mode '{}' does not exist".format(text))
            return
        view.print_mode(self.MODE)

    def print_routing_table(self):
        routing_table = self.protocol.routing_table.routing_table
        table = PrettyTable()
        table.field_names = ['destination', 'next_node', 'hops']
        for entry in routing_table:
            table.add_row(list(entry.values()))
        for entry in self.protocol.routing_table.unsupported_devices:
            table.add_row([entry, 'n/a', 'n/a'])
        print(table)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    protocol = ProtocolLite()

    messenger = Messenger(protocol)
    time.sleep(4)

    messenger.start_chatting()
