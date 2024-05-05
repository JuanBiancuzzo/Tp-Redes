import socket
from collections import deque
from math import ceil
import queue

from lib.parameter import SendMethod, OutputVerbosity
from lib.protocol.header import HEADER_SIZE
from lib.protocol.rdtp_segment import RDTPSegment
from lib.protocol.window import Window
from lib.errors import ProtocolError

PORT_INDEX = 1

# Ethernet MTU (1500) - IPv4 Header (20) - UDP Header (8)
#   este tamaño no cuenta nuestro propio header por lo que lo contiene
MAX_MSG = (1500 - 20 - 8) * 5

MAX_PAYLOAD = MAX_MSG - HEADER_SIZE
WINDOW_SIZE_SR = 5
WINDOW_SIZE_SW = 1
MAX_TIMEOUTS = 5

MAX_SENDING_QUEUE = 10

class RDTPStream:

    def __init__(self, socket, receiver_address, sequence_number, ack_number, method, logger):
        self.socket = socket
        self.receiver_address = receiver_address
        self.sequence_number = sequence_number
        self.ack_number = ack_number

        self.message_buffer = {}

        self.window = Window(
            WINDOW_SIZE_SR if method == SendMethod.SELECTIVE_REPEAT else WINDOW_SIZE_SW,
            socket,
            receiver_address,
            logger,
        )

        self.logger = logger

        self.send_queue = queue.Queue(MAX_SENDING_QUEUE)
        self.received_queue = queue.Queue()
        self.close_queue = queue.Queue(maxsize = 1)
        
        self.sent_close_message = False
        self.received_close_message = False

        self.num_timeouts = 0
    
    def recv_segment(self, timer):
        """
        Exception:
             * ProtocolError.ERROR_UNPACKING
        """
        self.socket.settimeout(timer)
        segment = None

        try:
            message, _ = self.socket.recvfrom(MAX_MSG)
            segment = RDTPSegment.deserialize(message) 
        except socket.timeout:
            pass

        self.socket.settimeout(None)
        return segment

    def send_payload(self, timer):
        if len(self.window.segments) > 10:
            return None

        try:
            return self.send_queue.get(timeout = timer)
        except:
            return None

    def recv(self, segment: RDTPSegment):
        """
        Exception:
            * ProtocolError.ERROR_PACKING
            * ProtocolError.ERROR_SENDING_MESSAGE
        """

        # tanto los mensajes de ack como los mensajes de fin-ack entran acá
        if segment.header.ack:
            segments_remove = self.window.remove_acked_segments(segment.header.ack_num)
            self.logger.log(OutputVerbosity.VERBOSE, f"Ack message received: {segment.header.ack_num}")

            if segments_remove > 0:
                self.logger.log(OutputVerbosity.VERBOSE, f"Received new ack message, sending new batch of segments")
                self.window.send_new_batch()
                self.num_timeouts = 0

            else:
                self.logger.log(OutputVerbosity.VERBOSE, f"Received repeated ack message, re-sending oldest segment in window")
                self.window.resend_oldest_segment()

        elif segment.header.fin:
            # solo se manda el fin después de haber recibido ack de todos los mensajes
            if segment.header.seq_num != self.ack_number:
                # puede ser que no le llego el fin ack
                # raise error
                pass

            self.ack_number += 1
            
            self.logger.log(OutputVerbosity.VERBOSE, "Receving end closing")
            fin_ack_message = RDTPSegment.create_fin_ack_message(
                self.get_src_port(), 
                self.get_destination_port(), 
                self.sequence_number, 
                self.ack_number
            )

            try:
                self.socket.sendto(fin_ack_message.serialize(), self.receiver_address)
            except socket.error:
                raise ProtocolError.ERROR_SENDING_MESSAGE      

            self.logger.log(OutputVerbosity.VERBOSE, f"Fin-ack message sent {fin_ack_message.header.ack_num}")
            self.received_close_message = True                  
        
        # No tenes ninguna flag
        elif segment.header.seq_num == self.ack_number:
            self.logger.log(OutputVerbosity.VERBOSE, f"Received segment: {segment.header.seq_num}")

            if not segment.header.ping:
                self.ack_number += len(segment.bytes)
                self.received_queue.put(segment.bytes)
            else:
                self.logger.log(OutputVerbosity.VERBOSE, f"Ping received")
                self.ack_number += 1
            
            self.integrate_buffered_messages()
            
            ack_message = RDTPSegment.create_ack_message(
                self.get_src_port(), 
                self.get_destination_port(), 
                self.sequence_number, 
                self.ack_number            
            )
            self.logger.log(OutputVerbosity.VERBOSE, f"Ack sent: {ack_message.header.ack_num}")
            
            try:
                self.socket.sendto(ack_message.serialize(), self.receiver_address)
            except socket.error:
                raise ProtocolError.ERROR_SENDING_MESSAGE
        
        else:
            self.logger.log(OutputVerbosity.VERBOSE, f"Received incorrect ack message, expected: {self.ack_number} received: {segment.header.seq_num}")
            if len(self.message_buffer) < self.window.max() and segment.header.seq_num > self.ack_number:
                self.message_buffer[segment.header.seq_num] = segment
            
            repeated_ack_message = RDTPSegment.create_ack_message(
                self.get_src_port(), 
                self.get_destination_port(), 
                self.sequence_number, 
                self.ack_number
            )
            self.logger.log(OutputVerbosity.VERBOSE, f"Received message with wrong sequence number. Ack sent: {repeated_ack_message.header.ack_num}")

    def send_fin_message(self):
        """
        Exception:
            * ProtocolError.ERROR_PACKING
            * ProtocolError.ERROR_SENDING_MESSAGE
        """

        self.logger.log(OutputVerbosity.VERBOSE, "Sending end closing")
        fin_message = RDTPSegment.create_fin_message(
            self.get_src_port(), 
            self.get_destination_port(), 
            self.sequence_number, 
            self.ack_number
        )

        self.sequence_number += 1
        self.window.add_segment(fin_message)

        self.window.send_new_batch()
        self.sent_close_message = True

    def send_ping_message(self):
        """
        Exception:
            * ProtocolError.ERROR_PACKING
            * ProtocolError.ERROR_SENDING_MESSAGE
        """

        self.logger.log(OutputVerbosity.VERBOSE, "Sending ping message")
        fin_message = RDTPSegment.create_ping_message(
            self.get_src_port(), 
            self.get_destination_port(), 
            self.sequence_number, 
            self.ack_number
        )

        self.sequence_number += 1
        self.window.add_segment(fin_message)

        self.window.send_new_batch()

    def send(self, message: bytes):
        """
        Exception:
            * ProtocolError.ERROR_EMPTY_MESSAGE
            * ProtocolError.ERROR_PACKING
            * ProtocolError.ERROR_SENDING_MESSAGE
        """

        num_segments = ceil(len(message) / MAX_PAYLOAD)
        self.logger.log(OutputVerbosity.VERBOSE, f"Sending {num_segments} segments")
        
        if num_segments <= 0:
            raise ProtocolError.ERROR_EMPTY_MESSAGE
        
        # Creo los segmentos y los guardo en una cola
        for _ in range(num_segments):
            segment_data = message[:MAX_PAYLOAD]
            message = message[MAX_PAYLOAD:]

            segment = RDTPSegment.create_new_message(
                self.get_src_port(), 
                self.get_destination_port(), 
                self.sequence_number, 
                self.ack_number, 
                segment_data
            )

            self.sequence_number += len(segment.bytes)
            self.window.add_segment(segment)
        
        self.window.send_new_batch()
        
    def integrate_buffered_messages(self):
        """
        Takes the buffered messages and based on the current ack number, it integrates them into the received message.
        The message buffer is a dictionary where the key is the sequence number of the message and the value is the message itself.
        It updates the value in last with true if the last segment is added to the byte stream.
        """
        
        while self.ack_number in self.message_buffer:
            message_to_add = self.message_buffer[self.ack_number]
                
            self.logger.log(OutputVerbosity.VERBOSE, f"Segment integrated {message_to_add.header.seq_num}")
            self.received_queue.put(message_to_add.bytes)
            del self.message_buffer[self.ack_number]
            
            self.ack_number += len(message_to_add.bytes)
            self.logger.log(OutputVerbosity.VERBOSE, f"Ack number updated to: {self.ack_number}")

    def check_times(self, current_time_ns):        
        if self.window.check_timeouts(current_time_ns):
            self.num_timeouts += 1

            if self.num_timeouts >= MAX_TIMEOUTS:
                raise ProtocolError.ERROR_RECEIVING_END_DEAD  

            self.logger.log(OutputVerbosity.VERBOSE, f"Timeout, re-sending oldest segment in window")
            self.window.resend_oldest_segment()

    def get_src_port(self):
        return self.socket.getsockname()[PORT_INDEX]
    
    def get_destination_port(self):
        return self.receiver_address[PORT_INDEX]
    