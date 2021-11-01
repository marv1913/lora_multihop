import socket
import time


class PerformanceTest:
    REGISTRATION_MESSAGE = 'Registration,{peer_id},true|'
    REGISTERED_PEERS = 'registeredPeers?|'
    CONNECTION_REQUEST = 'ConnectRequest,{source_peer_id},{target_peer_id},60|'

    def __init__(self, host_node_a, ipc_port_node_a, message_port_node_a, host_node_b, ipc_port_node_b,
                 message_port_node_b):
        self.ipc_socket_node_a = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ipc_socket_node_a.connect((host_node_a, ipc_port_node_a))

        self.message_socket_node_a = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.message_socket_node_a.connect((host_node_a, message_port_node_a))

        self.ipc_socket_node_b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ipc_socket_node_b.connect((host_node_b, ipc_port_node_b))

        self.message_socket_node_b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.message_socket_node_b.connect((host_node_b, message_port_node_b))

    def start_performance_test(self, message_list):
        result_list = []
        for message in message_list:
            print(f'sending message: {message}')
            self.message_socket_node_a.send(str_to_bytes(message))
            start_time = time.time()
            received_message = self.message_socket_node_b.recv(1024).decode('utf-8')
            print(len(received_message))
            print(len(message))
            if len(received_message) < len(message):
                while True:
                    print('receive again')
                    print(received_message)
                    data = self.message_socket_node_b.recv(1024).decode('utf-8')
                    if not data:
                        return
                    received_message = received_message + data
                    print(len(received_message))
                    print(len(message))
                    if not len(received_message) < len(message):
                        break

            print(received_message)
            end_time = time.time()
            result_list.append(end_time-start_time)
        return result_list, sum(result_list) / len(result_list)


def str_to_bytes(str_to_convert):
    return str_to_convert.encode('utf-8')


if __name__ == '__main__':
    performance_test = PerformanceTest('192.168.178.200', 6000, 6100, '192.168.178.201', 6000, 6100)
    result = performance_test.start_performance_test(['h']*10)
    print(result)