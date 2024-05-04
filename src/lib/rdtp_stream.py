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

        self.send_queue = queue.Queue()
        self.received_queue = queue.Queue()
        self.close_queue = queue.Queue(maxsize = 1)
        
        self.sent_close_message = False
        self.received_close_message = False
    
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
        try:
            return self.send_queue.get(timeout = timer)
        except:
            return None

    def recv(self, segment, message_buffer):
        """
        Exception:
            * ProtocolError.ERROR_PACKING
            * ProtocolError.ERROR_SENDING_MESSAGE
        """

        self.logger.log(OutputVerbosity.VERBOSE, f"entre al recv con método {self.method} en el thread")
        if self.method == SendMethod.STOP_WAIT:
            self.recv_stop_wait(segment)
        else:
            self.recv_selective_repeat(segment, message_buffer)

    def get_src_port(self):
        return self.socket.getsockname()[PORT_INDEX]
    
    def get_destination_port(self):
        return self.receiver_address[PORT_INDEX]
        
    def send(self, message: bytes):
        """
        Exception:
            * ProtocolError.ERROR_EMPTY_MESSAGE
            * ProtocolError.ERROR_PACKING
            * ProtocolError.ERROR_UNPACKING
            * ProtocolError.ERROR_SENDING_MESSAGE
            * ProtocolError.ERROR_RECEIVING_MESSAGE
        """

        if self.method == SendMethod.STOP_WAIT:
            self.send_stop_wait(message)
        else:
            self.send_selective_repeat(message)
        
    def send_stop_wait(self, message: bytes):
        """
        Exception:
            * ProtocolError.ERROR_EMPTY_MESSAGE
            * ProtocolError.ERROR_PACKING
            * ProtocolError.ERROR_UNPACKING
            * ProtocolError.ERROR_SENDING_MESSAGE
            * ProtocolError.ERROR_RECEIVING_MESSAGE
        """

        self.socket.settimeout(TIMEOUT)
        
        num_segments = ceil(len(message) / MAX_PAYLOAD)
        self.logger.log(OutputVerbosity.VERBOSE, f"voy a mandar {num_segments} segmentos con stop and wait")
        
        if num_segments <= 0:
            raise ProtocolError.ERROR_EMPTY_MESSAGE
        
        for i in range(num_segments):
            segment_data = message[i * MAX_PAYLOAD : (i + 1) * MAX_PAYLOAD]
            segment = RDTPSegment.create_new_message(self.get_src_port(), self.get_destination_port(), self.sequence_number, self.ack_number, segment_data)
            
            self.logger.log(OutputVerbosity.VERBOSE, f"mande el segmento {segment.header.seq_num}")
            try:
                self.socket.sendto(segment.serialize(), self.receiver_address)
            except socket.error:
                raise ProtocolError.ERROR_SENDING_MESSAGE
            
            self.sequence_number += len(segment_data)
           
            while True:
                try:
                    self.logger.log(OutputVerbosity.VERBOSE, f"esperando ack del segmento {segment.header.seq_num}")
                    answer, _ = self.socket.recvfrom(MAX_MSG)
                    ack_message = RDTPSegment.deserialize(answer)
                    
                except socket.timeout:
                    self.logger.log(OutputVerbosity.VERBOSE, f"timeout, reenviando el segmento {segment.header.seq_num}")
                    try:
                        self.socket.sendto(segment.serialize(), self.receiver_address)
                    except socket.error:
                        raise ProtocolError.ERROR_SENDING_MESSAGE

                    continue
                    
                except socket.error:
                    raise ProtocolError.ERROR_RECEIVING_MESSAGE

                if ack_message.header.ack_num == self.sequence_number:
                    self.logger.log(OutputVerbosity.VERBOSE, f"recibi el ack {ack_message.header.ack_num}")
                    break
                else:
                    self.logger.log(OutputVerbosity.VERBOSE, f"ack incorrecto, esperaba {self.sequence_number} pero recibi {ack_message.header.ack_num}. Reenvío el segmento {segment.header.seq_num}")
                    try:
                        self.socket.sendto(segment.serialize(), self.receiver_address)
                    except:
                        raise ProtocolError.ERROR_SENDING_MESSAGE
                    
                    continue
        
        self.logger.log(OutputVerbosity.VERBOSE, "termine de mandar los segmentos")

    def send_selective_repeat(self, message: bytes):
        """
        Exception:
            * ProtocolError.ERROR_EMPTY_MESSAGE
            * ProtocolError.ERROR_PACKING
            * ProtocolError.ERROR_UNPACKING
            * ProtocolError.ERROR_SENDING_MESSAGE
            * ProtocolError.ERROR_RECEIVING_MESSAGE
        """

        self.socket.settimeout(TIMEOUT)
        
        num_segments = ceil(len(message) / MAX_PAYLOAD)
        self.logger.log(OutputVerbosity.VERBOSE, f"voy a mandar {num_segments} segmentos con selective repeat")
        
        if num_segments <= 0:
            raise ProtocolError.ERROR_EMPTY_MESSAGE

        segments = deque()
        window = Window(WINDOW_SIZE)
        
        # Creo los segmentos y los guardo en una cola
        for i in range(num_segments):
            segment_data = message[i * MAX_PAYLOAD : (i + 1) * MAX_PAYLOAD]
            segment = RDTPSegment.create_new_message(self.get_src_port(), self.get_destination_port(), self.sequence_number, self.ack_number, segment_data)
            self.sequence_number += len(segment_data)
            segments.append(segment)
        
        self.send_new_batch(window, segments)
                
        while len(window) > 0:            
            try:
                message, _ = self.socket.recvfrom(MAX_MSG)
                ack_message = RDTPSegment.deserialize(message)
                self.logger.log(OutputVerbosity.VERBOSE, f"recibi el ack {ack_message.header.ack_num}")

            except socket.timeout:
                self.logger.log(OutputVerbosity.VERBOSE, f"timeout, reenviando el segmento más viejo")
                self.resend_oldest_segment(window)
                continue

            except socket.error:
                raise ProtocolError.ERROR_RECEIVING_MESSAGE
            
            lenght_before_removal = len(window)
            window.remove_acked_segments(ack_message.header.ack_num)
            
            # Si recibieron algún segmento en orden, mínimamente nos mandaran el ack del primer segmento en la ventana.
            if lenght_before_removal > len(window):
                self.logger.log(OutputVerbosity.VERBOSE, f"ack nuevo, mandando nuevos segmentos")
                self.send_new_batch(window, segments)
            # Si no cambió la longitud, entonces nos mandaron un ack repetido.
            else:
                self.logger.log(OutputVerbosity.VERBOSE, f"ack repetido, reenvío el más viejo")
                self.resend_oldest_segment(window)

    def send_new_batch(self, window, segments):
        '''
        Llenamos la ventana con los siguientes segmentos a enviar y los enviamos.

        Exception:
            * ProtocolError.ERROR_PACKING
            * ProtocolError.ERROR_SENDING_MESSAGE
        '''

        while not window.is_full() and len(segments) > 0:
            segment_to_send = segments.popleft()

            self.logger.log(OutputVerbosity.VERBOSE, f"mande el segmento {segment_to_send.header.seq_num}")

            try:
                self.socket.sendto(segment_to_send.serialize(), self.receiver_address)
            except socket.error:
                raise ProtocolError.ERROR_SENDING_MESSAGE
            
            window.add_segment(segment_to_send)

    def resend_oldest_segment(self, window):
        """
        Exception:
            * ProtocolError.ERROR_PACKING
            * ProtocolError.ERROR_SENDING_MESSAGE
        """

        oldest_segment = window.get_oldest_segment()
        self.logger.log(OutputVerbosity.VERBOSE, f"reenviando el segmento {oldest_segment.header.seq_num}")
        
        try:
            self.socket.sendto(oldest_segment.serialize(), self.receiver_address)    
        except socket.error:
            raise ProtocolError.ERROR_SENDING_MESSAGE

    def send_fin_ack_message(self):
        """
        Exception:
            * ProtocolError.ERROR_PACKING
            * ProtocolError.ERROR_SENDING_MESSAGE
        """

        self.ack_number += 1
        self.received_close_message = True
        fin_ack_message = RDTPSegment.create_fin_ack_message(self.get_src_port(), self.get_destination_port(), self.sequence_number, self.ack_number)
        self.logger.log(OutputVerbosity.VERBOSE, f"mande el fin-ack {fin_ack_message.header.ack_num}")
        
        try:
            self.socket.sendto(fin_ack_message.serialize(), self.receiver_address)
        except socket.error:
            raise ProtocolError.ERROR_SENDING_MESSAGE

    def recv_stop_wait(self, segment):
        """
        Exception:
            * ProtocolError.ERROR_PACKING
            * ProtocolError.ERROR_SENDING_MESSAGE
        """
        
        self.logger.log(OutputVerbosity.VERBOSE, "empezando a recibir los segmentos en stop and wait")
        
        if segment.header.seq_num == self.ack_number:
            self.logger.log(OutputVerbosity.VERBOSE, f"recibi el segmento {segment.header.seq_num}")
            
            if segment.header.fin:
                self.send_fin_ack_message()
            else:
                self.ack_number += len(segment.bytes)
                self.received_queue.put(segment.bytes)
                ack_message = RDTPSegment.create_ack_message(self.get_src_port(), self.get_destination_port(), self.sequence_number, self.ack_number)
                self.logger.log(OutputVerbosity.VERBOSE, f"mande el ack {ack_message.header.ack_num}")
                
                try:
                    self.socket.sendto(ack_message.serialize(), self.receiver_address)
                except socket.error:
                    raise ProtocolError.ERROR_SENDING_MESSAGE
        else:
            self.logger.log(OutputVerbosity.VERBOSE, f"segmento incorrecto, esperaba {self.ack_number} pero recibi {segment.header.seq_num}")
            repeated_ack_message = RDTPSegment.create_ack_message(self.get_src_port(), self.get_destination_port(), self.sequence_number, self.ack_number)
            self.logger.log(OutputVerbosity.VERBOSE, f"Me mandaron un mensaje con seq number equivocado. Mande el ack {repeated_ack_message.header.ack_num}")
                        
    def recv_selective_repeat(self, segment, message_buffer):
        """
        Exception:
            * ProtocolError.ERROR_PACKING
            * ProtocolError.ERROR_SENDING_MESSAGE
        """

        self.logger.log(OutputVerbosity.VERBOSE, "empezando a recibir los segmentos en selective repeat")
    
        if segment.header.seq_num == self.ack_number:
            self.logger.log(OutputVerbosity.VERBOSE, f"recibi el segmento {segment.header.seq_num}")
            
            if segment.header.fin:
                self.send_fin_ack_message()
            else:
                self.ack_number += len(segment.bytes)
                self.received_queue.put(segment.bytes)
                
                self.integrate_buffered_messages(message_buffer)
                
                ack_message = RDTPSegment.create_ack_message(self.get_src_port(), self.get_destination_port(), self.sequence_number, self.ack_number)
                self.logger.log(OutputVerbosity.VERBOSE, f"mande el ack {ack_message.header.ack_num}")
                
                try:
                    self.socket.sendto(ack_message.serialize(), self.receiver_address)
                except socket.error:
                    raise ProtocolError.ERROR_SENDING_MESSAGE
        else:
            self.logger.log(OutputVerbosity.VERBOSE, f"segmento incorrecto, esperaba {self.ack_number} pero recibi {segment.header.seq_num}")
            if len(message_buffer) < WINDOW_SIZE and segment.header.seq_num not in message_buffer:
                message_buffer[segment.header.seq_num] = segment
            
            repeated_ack_message = RDTPSegment.create_ack_message(self.get_src_port(), self.get_destination_port(), self.sequence_number, self.ack_number)
            self.logger.log(OutputVerbosity.VERBOSE, f"Me mandaron un mensaje con seq number equivocado. Mande el ack {repeated_ack_message.header.ack_num}")
        
    def integrate_buffered_messages(self, message_buffer):
        """
        Takes the buffered messages and based on the current ack number, it integrates them into the received message.
        The message buffer is a dictionary where the key is the sequence number of the message and the value is the message itself.
        It updates the value in last with true if the last segment is added to the byte stream.
        """
        while True:
            if self.ack_number in message_buffer:
                message_to_add = message_buffer[self.ack_number]
                
                self.logger.log(OutputVerbosity.VERBOSE, f"integro el segmento {message_to_add.header.seq_num}")
                self.received_queue.put(message_to_add.bytes)
                del message_buffer[self.ack_number]
                
                self.ack_number += len(message_to_add.bytes)
                self.logger.log(OutputVerbosity.VERBOSE, f"ack number actualizado a {self.ack_number}")
            else:
                break

    def close(self):
        """
        Exception:
            * ProtocolError.ERROR_PACKING
            * ProtocolError.ERROR_UNPACKING
            * ProtocolError.ERROR_SENDING_MESSAGE
            * ProtocolError.ERROR_RECEIVING_MESSAGE
        """
        self.socket.settimeout(TIMEOUT)

        self.logger.log(OutputVerbosity.VERBOSE, "Cerrando el stream")
        fin_message = RDTPSegment.create_fin_message(self.get_src_port(), self.get_destination_port(), self.sequence_number, self.ack_number)
        
        try:
            self.socket.sendto(fin_message.serialize(), self.receiver_address)
        except socket.error:
            raise ProtocolError.ERROR_SENDING_MESSAGE
        
        self.sequence_number += 1

        while True:
            try:
                message, _ = self.socket.recvfrom(MAX_MSG)
                fin_ack_message = RDTPSegment.deserialize(message)
                if fin_ack_message.header.fin and fin_ack_message.header.ack and fin_ack_message.header.ack_num == self.sequence_number:
                    self.logger.log(OutputVerbosity.VERBOSE, "Recibi el fin-ack")
                    break
            except socket.timeout:
                self.logger.log(OutputVerbosity.VERBOSE, "Timeout, reenviando el fin")
                
                try:
                    self.socket.sendto(fin_message.serialize(), self.receiver_address)
                except socket.error:
                    raise ProtocolError.ERROR_SENDING_MESSAGE
                
                continue
    
            except socket.error:
                raise ProtocolError.ERROR_RECEIVING_MESSAGE

        self.socket.settimeout(None)
        self.sent_close_message = True