from socket import *
from lib.parameter import SendMethod, OutputVerbosity
from lib.logger import Logger

SRC_PORT_INDEX = 1
MAX_MSG = 1472 # Ethernet MTU (1500) - IPv4 Header (20) - UDP Header (8), este tamaño contiene nuestro propio header.
WINDOW_SIZE = 5

class RDTPStream:
    def __init__(self, socket, receiver_address, sequence_number, ack_number, method, logger):
        self.socket = socket
        self.receiver_address = receiver_address
        self.sequence_number = sequence_number
        self.ack_number = ack_number

        self.method = method
        self.logger = logger

    def get_src_port(self):
        return self.socket.getsockname()[SRC_PORT_INDEX]
    
    def send(self, message: bytes):
        if self.method == SendMethod.STOP_WAIT:
            self.send_stop_wait(message)
        else:
            self.send_selective_repeat(message)
            
    def recv(self, size: int) -> bytes:
        if self.method == SendMethod.STOP_WAIT:
            return self.recv_stop_wait(size)
        else:
            return self.recv_selective_repeat(size)
        
    def send_stop_wait(self, message: bytes):
        pass

    def recv_stop_wait(self, size: int) -> bytes:
        pass
    
    def send_selective_repeat(self, message: bytes):
        pass

    def recv_selective_repeat(self, size: int) -> bytes:
        pass