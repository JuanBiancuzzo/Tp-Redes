from socket import *
from lib.rdtp import SRC_PORT_INDEX 

class RDTPStream:
    def __init__(self, socket, receiver_address, sequence_number, ack_number):
        self.socket = socket
        self.receiver_address = receiver_address
        self.sequence_number = sequence_number
        self.ack_number = ack_number

    def send(self, message: bytes):
        pass

    def recv(self, size: int) -> bytes:
        pass

    def get_src_port(self):
        return self.socket.getsockname()[SRC_PORT_INDEX]
