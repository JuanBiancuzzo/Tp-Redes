import socket
from collections import deque

from lib.errors import ProtocolError
from lib.parameter import OutputVerbosity

class Window:
    def __init__(self, size: int, socket, receiver_address, logger):
        self.size = size
        self.window = deque()
        self.segments = deque()
        
        self.socket = socket
        self.receiver_address = receiver_address
        
        self.logger = logger
    
    def max(self):
        return self.size
        
    def add_segment(self, segment):
        self.segments.append(segment)
    
    # Si el tamaño no cambia me mandaron un ack de uno que ya me ackearon, por lo que se perdió el siguiente.
    def remove_acked_segments(self, ack_number) -> int:
        num_ack_remove = 0
        while len(self.window) > 0 and self.window[0].header.seq_num < ack_number:
            self.window.popleft()
            num_ack_remove += 1

        return num_ack_remove

    def send_new_batch(self):
        '''
        Filling the window with the segments to be sent and sends them.

        Exception:
            * ProtocolError.ERROR_PACKING
            * ProtocolError.ERROR_SENDING_MESSAGE
        '''

        while not self.window_is_full() and len(self.segments) > 0:
            segment_to_send = self.segments.popleft()

            self.logger.log(OutputVerbosity.VERBOSE, f"Sent segment: {segment_to_send.header.seq_num}")

            try:
                self.socket.sendto(segment_to_send.serialize(), self.receiver_address)
            except socket.error:
                raise ProtocolError.ERROR_SENDING_MESSAGE
            
            self.window.append(segment_to_send)

    def resend_oldest_segment(self):
        """
        Exception:
            * ProtocolError.ERROR_PACKING
            * ProtocolError.ERROR_SENDING_MESSAGE
        """

        oldest_segment = self.get_oldest_segment()
        self.logger.log(OutputVerbosity.VERBOSE, f"Re-sending segment: {oldest_segment.header.seq_num}")
        
        try:
            self.socket.sendto(oldest_segment.serialize(), self.receiver_address)    
        except socket.error:
            raise ProtocolError.ERROR_SENDING_MESSAGE

    def empty(self):
        return len(self.window) + len(self.segments) == 0

    def window_is_full(self):
        return len(self.window) >= self.size

    def get_oldest_segment(self):
        return self.window[0] if len(self.window) > 0 else None