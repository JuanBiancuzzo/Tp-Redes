from socket import *
from lib.parameter import SendMethod, OutputVerbosity
from lib.logger import Logger
from lib.protocol.header import Header, HEADER_SIZE
from lib.protocol.rdtp_segment import RDTPSegment
from lib.protocol.window import Window

from collections import deque

from math import ceil

PORT_INDEX = 1
MAX_MSG = 1472 # Ethernet MTU (1500) - IPv4 Header (20) - UDP Header (8), este tamaño contiene nuestro propio header.
MAX_PAYLOAD = MAX_MSG - HEADER_SIZE
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
        return self.socket.getsockname()[PORT_INDEX]
    
    def get_destination_port(self):
        return self.receiver_address[PORT_INDEX]
        
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
        num_segments = ceil(len(message) / MAX_PAYLOAD)
        
        if num_segments <= 0:
            #raise error
            pass
                
        segments = deque()
        window = Window(WINDOW_SIZE)
        
        for i in range(num_segments):
            segment_data = message[i * MAX_PAYLOAD : (i + 1) * MAX_PAYLOAD]
            is_last = True if i == num_segments - 1 else False
            segment = RDTPSegment.create_new_message(self.get_src_port(), self.get_destination_port(), self.sequence_number, self.ack_number, is_last, segment_data)
            self.sequence_number += len(segment_data)
            segments.append(segment)
        
        fill_window(window, segments)
        
        for segment in window:
            self.socket.sendto(segment.serialize(), self.receiver_address)
            self.logger.log(OutputVerbosity.VERBOSE, f"mande el segmento {segment.header.seq_num}")
                
        while len(window) > 0:
            message, _ = self.socket.recvfrom(MAX_MSG)
            ack_message = RDTPSegment.deserialize(message)
            self.logger.log(OutputVerbosity.VERBOSE, f"recibi el ack {ack_message.header.ack_num}")
            window.remove_acked_segments(ack_message.header.ack_num)
            fill_window(window, segments)
            
            for segment in window:
                self.socket.sendto(segment.serialize(), self.receiver_address)
                self.logger.log(OutputVerbosity.VERBOSE, f"mande el segmento {segment.header.seq_num}")

    def recv_selective_repeat(self, size: int) -> bytes:
        received_message = bytearray()
        message_buffer = []
        
        self.socket.recvfrom(MAX_MSG)
        
        
def fill_window(window, segments):
        while not window.is_full() and len(segments) > 0:
            window.add_segment(segments.popleft())