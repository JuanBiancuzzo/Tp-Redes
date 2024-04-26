from socket import *
from lib.parameter import SendMethod, OutputVerbosity
from lib.logger import Logger

SRC_PORT_INDEX = 1
MAX_MSG = 2**16 - 8 # 65528

class RDTPStream:
    def __init__(self, socket, receiver_address, sequence_number, ack_number, method, logger):
        self.socket = socket
        self.receiver_address = receiver_address
        self.sequence_number = sequence_number
        self.ack_number = ack_number

        self.method = method
        self.logger = logger

    def send(self, message: bytes):
        pass

    def recv(self, size: int) -> bytes:
        pass

    def get_src_port(self):
        return self.socket.getsockname()[SRC_PORT_INDEX]
