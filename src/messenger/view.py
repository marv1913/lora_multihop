import messenger

__author__ = "Marvin Rausch"

WELCOME_TEXT = """
 _        _______  _______  _______               __________________ _       __________________         
( \      (  ___  )(  ____ )(  ___  )     |\     /|\__   __/\__   __/( \      \__   __/\__   __/|\     /|
| (      | (   ) || (    )|| (   ) |     | )   ( |   ) (      ) (   | (         ) (      ) (   ( \   / )
| |      | |   | || (____)|| (___) |     | |   | |   | |      | |   | |         | |      | |    \ (_) / 
| |      | |   | ||     __)|  ___  |     | |   | |   | |      | |   | |         | |      | |     \   /  
| |      | |   | || (\ (   | (   ) |     | |   | |   | |      | |   | |         | |      | |      ) (   
| (____/\| (___) || ) \ \__| )   ( |     | (___) |   | |   ___) (___| (____/\___) (___   | |      | |   
(_______/(_______)|/   \__/|/     \|_____(_______)   )_(   \_______/(_______/\_______/   )_(      \_/   
                                   (_____)                                                           \n"""


def print_mode(mode):
    if mode == messenger.messenger.CONFIG_MODE:
        print('config mode entered')
    if mode == messenger.messenger.SEND_MODE:
        print('send mode entered')
    if mode == messenger.messenger.LIST_MODE:
        print('list mode entered')


def print_help_text():
    print('\nthere are 2 modes:\n'
          '     send mode   -   :s\n'
          '     config mode -   :c\n\n'
          'e.g. to enter the send mode type in ":s"\n\n'
          'in send mode you can type in a text which is sended to the address which was set by the user\n'
          ''
          'in config mode you have three options:\n'
          '     "all"   to see all available addresses\n'
          '     "?"     to get set address\n'
          '     type in a address to change destination address\n'
          '\n'
          'in each mode you can type ":l" to get the current routing table\n')


def print_welcome_text():
    print(WELCOME_TEXT)
    print("type 'help' to see how this program works:\n")


def display_received_message(message_header_obj):
    print(f'*******************received message from {message_header_obj.source}: {message_header_obj.payload}*****'
          f'**************')


def print_ack_text():
    print('*******************message was acknowledged by receiver*******************')
