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
TIMEOUT = 1

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
        print("entre al recv con método", self.method)
        if self.method == SendMethod.STOP_WAIT:
            return self.recv_stop_wait(size)
        else:
            return self.recv_selective_repeat(size)
        
    def send_stop_wait(self, message: bytes):
        self.socket.settimeout(TIMEOUT)
        
        num_segments = ceil(len(message) / MAX_PAYLOAD)
        print("num_segments", num_segments)
        
        if num_segments <= 0:
            #raise error
            pass
        
        for i in range(num_segments):
            segment_data = message[i * MAX_PAYLOAD : (i + 1) * MAX_PAYLOAD]
            is_last = True if i == num_segments - 1 else False
            segment = RDTPSegment.create_new_message(self.get_src_port(), self.get_destination_port(), self.sequence_number, self.ack_number, is_last, segment_data)
            
            self.logger.log(OutputVerbosity.VERBOSE, f"mande el segmento {segment.header.seq_num}")
            self.socket.sendto(segment.serialize(), self.receiver_address)
            self.sequence_number += len(segment_data)
           
            while True:
                try:
                    self.logger.log(OutputVerbosity.VERBOSE, f"esperando ack del segmento {segment.header.seq_num}")
                    answer, _ = self.socket.recvfrom(MAX_MSG)
                    ack_message = RDTPSegment.deserialize(answer)
                    if ack_message.header.ack_num == self.sequence_number:
                        self.logger.log(OutputVerbosity.VERBOSE, f"recibi el ack {ack_message.header.ack_num}")
                        break
                    else:
                        self.logger.log(OutputVerbosity.VERBOSE, f"ack incorrecto, esperaba {self.sequence_number} pero recibi {ack_message.header.ack_num}. Reenvío el segmento {segment.header.seq_num}")
                        self.socket.sendto(segment.serialize(), self.receiver_address)
                        continue
                except timeout:
                    self.logger.log(OutputVerbosity.VERBOSE, f"timeout, reenviando el segmento {segment.header.seq_num}")
                    self.socket.sendto(segment.serialize(), self.receiver_address)
                    continue
        
        self.logger.log(OutputVerbosity.VERBOSE, "termine de mandar los segmentos")


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
                
        while len(window) > 0:
            for segment in window:
                self.socket.sendto(segment.serialize(), self.receiver_address)
                self.logger.log(OutputVerbosity.VERBOSE, f"mande el segmento {segment.header.seq_num}")
            
            message, _ = self.socket.recvfrom(MAX_MSG)
            ack_message = RDTPSegment.deserialize(message)
            self.logger.log(OutputVerbosity.VERBOSE, f"recibi el ack {ack_message.header.ack_num}")
            window.remove_acked_segments(ack_message.header.ack_num)
            fill_window(window, segments)

        pass

    def recv_stop_wait(self, size: int) -> bytes:
        received_message = bytearray()
        
        while True:
            message, _ = self.socket.recvfrom(MAX_MSG)
            segment = RDTPSegment.deserialize(message)
            
            if segment.header.seq_num == self.ack_number:
                self.logger.log(OutputVerbosity.VERBOSE, f"recibi el segmento {segment.header.seq_num}")
                self.ack_number += len(segment.bytes)
                received_message += segment.bytes
                
                ack_message = RDTPSegment.create_ack_message(self.get_src_port(), self.get_destination_port(), self.sequence_number, self.ack_number)
                self.logger.log(OutputVerbosity.VERBOSE, f"mande el ack {ack_message.header.ack_num}")
                self.socket.sendto(ack_message.serialize(), self.receiver_address)
                
                if segment.header.is_last:
                    break
            else:
                self.logger.log(OutputVerbosity.VERBOSE, f"segmento incorrecto, esperaba {self.ack_number} pero recibi {segment.header.seq_num}")
                repeated_ack_message = RDTPSegment.create_ack_message(self.get_src_port(), self.get_destination_port(), self.sequence_number, self.ack_number)
                self.logger.log(OutputVerbosity.VERBOSE, f"Me mandaron un mensaje con seq number equivocado. Mande el ack {repeated_ack_message.header.ack_num}")
                
        self.logger.log(OutputVerbosity.VERBOSE, "termine de recibir los segmentos")
        return received_message
    
    
        
    def recv_selective_repeat(self, size: int) -> bytes:
        received_message = bytearray()
        message_buffer = {}
        
        while True:
            message, _ = self.socket.recvfrom(MAX_MSG)
            segment = RDTPSegment.deserialize(message)
            last = segment.header.is_last
        
            if segment.header.seq_num == self.ack_number:
                self.logger.log(OutputVerbosity.VERBOSE, f"recibi el segmento {segment.header.seq_num}")
                self.ack_number += len(segment.bytes)
                received_message += segment.bytes
                
                self.integrate_buffered_messages(message_buffer, received_message, last)
                
                ack_message = RDTPSegment.create_ack_message(self.get_src_port(), self.get_destination_port(), self.sequence_number, self.ack_number)
                self.logger.log(OutputVerbosity.VERBOSE, f"mande el ack {ack_message.header.ack_num}")
                self.socket.sendto(ack_message.serialize(), self.receiver_address)
                
                if last:
                    break
            else:
                self.logger.log(OutputVerbosity.VERBOSE, f"segmento incorrecto, esperaba {self.ack_number} pero recibi {segment.header.seq_num}")
                if len(message_buffer) < WINDOW_SIZE and segment.header.seq_num not in message_buffer:
                    message_buffer[segment.header.seq_num] = segment
                repeated_ack_message = RDTPSegment.create_ack_message(self.get_src_port(), self.get_destination_port(), self.sequence_number, self.ack_number)
                self.logger.log(OutputVerbosity.VERBOSE, f"Me mandaron un mensaje con seq number equivocado. Mande el ack {repeated_ack_message.header.ack_num}")
        pass
    
    def integrate_buffered_messages(self, message_buffer, received_message, last):
        '''
        Takes the buffered messages and based on the current ack number, it integrates them into the received message.
        The message buffer is a dictionary where the key is the sequence number of the message and the value is the message itself.
        I updates the value in last with true if the last segment is added to the byte stream.
        '''
        while True:
            if self.ack_number in message_buffer:
                message_to_add = message_buffer[self.ack_number]
                self.logger.log(OutputVerbosity.VERBOSE, f"integro el segmento {message_to_add.header.seq_num}")
                received_message += message_to_add.bytes
                del message_buffer[self.ack_number]
                self.ack_number += len(message_to_add.bytes)
                self.logger.log(OutputVerbosity.VERBOSE, f"ack number actualizado a {self.ack_number}")
                if message_to_add.header.is_last:
                    self.logger.log(OutputVerbosity.VERBOSE, "Encontré el último segmento")
                    last = True
        
        
def fill_window(window, segments):
        while not window.is_full() and len(segments) > 0:
            window.add_segment(segments.popleft())