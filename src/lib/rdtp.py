from socket import socket, AF_INET, SOCK_DGRAM

from lib.protocol.header import Header, HEADER_SIZE
from lib.protocol.rdtp_segment import RDTPSegment
from lib.logger import Logger
from lib.parameter import OutputVerbosity
from lib.protocol.window import TIMEOUT
from lib.manage_stream import create_stream

from lib.errors import ProtocolError

import random

SRC_PORT_INDEX = 1

class RDTP:
    def __init__(self, method, logger: Logger):
        self.socket = socket(AF_INET, SOCK_DGRAM)

        self.method = method
        self.logger = logger
    
    # Para el cliente
    def connect(self, dest_ip, dest_port):
        """
        Exception:  
            * ProtocolError.ERROR_PACKING
            * ProtocolError.ERROR_UNPACKING
            * ProtocolError.ERROR_SENDING_MESSAGE
            * ProtocolError.ERROR_RECEIVING_MESSAGE
            * ProtocolError.ERROR_HANDSHAKE
        """

        src_port = self.socket.getsockname()[SRC_PORT_INDEX]
        sequence_number = RDTP.generate_initial_sequence_number()
        syn_message = RDTPSegment.create_syn_message(src_port, dest_port, sequence_number)
        
        try:
            self.socket.sendto(syn_message.serialize(), (dest_ip, dest_port))
        except socket.error:
            raise ProtocolError.ERROR_SENDING_MESSAGE

        self.logger.log(OutputVerbosity.VERBOSE, f"Syn message sent to: {dest_ip}:{dest_port}")

        try:
            self.socket.settimeout(TIMEOUT)

            message, server_address = self.socket.recvfrom(HEADER_SIZE)
            self.socket.settimeout(None)
        except socket.timeout:
            raise ProtocolError.ERROR_HANDSHAKE
        except socket.error:
            raise ProtocolError.ERROR_RECEIVING_MESSAGE

        self.logger.log(OutputVerbosity.VERBOSE, "Received syn-ack message")

        header = Header.deserialize(message)
        ack_number = header.seq_num + 1

        # Reescribiendo para nuevo puerto
        server_address = (dest_ip, header.src_port)
        dest_port = header.src_port

        if header.syn and header.ack:

            sequence_number += 1
            ack_ack_message = RDTPSegment.create_ack_ack_message(src_port, dest_port, sequence_number, ack_number)

            try:
                self.socket.sendto(ack_ack_message.serialize(), server_address)
            except socket.error:
                raise ProtocolError.ERROR_SENDING_MESSAGE

            self.logger.log(OutputVerbosity.VERBOSE, "Ack-Ack message sent")

            return create_stream(self.socket, server_address, sequence_number, ack_number, self.method, self.logger)

        else:
            raise ProtocolError.ERROR_HANDSHAKE

    # Para el servidor
    def accept(self, ip, port):
        try:
            
            message, client_address = self.socket.recvfrom(HEADER_SIZE)
            self.logger.log(OutputVerbosity.VERBOSE, "Server: Syn message received")
            header = Header.deserialize(message)
            
            if header.syn:
                
                sequence_number = RDTP.generate_initial_sequence_number()
                ack_number = header.seq_num + 1
                dest_port = client_address[SRC_PORT_INDEX]

                new_client_socket = socket(AF_INET, SOCK_DGRAM)
                new_client_socket.bind((ip, 0))
                new_port = new_client_socket.getsockname()[SRC_PORT_INDEX]
                
                syn_ack_message = RDTPSegment.create_syn_ack_message(new_port, dest_port, sequence_number, ack_number)
                self.socket.sendto(syn_ack_message.serialize(), client_address)
                self.logger.log(OutputVerbosity.VERBOSE, "Server: Syn-Ack message sent")
                
                message, client_address = new_client_socket.recvfrom(HEADER_SIZE)
                self.logger.log(OutputVerbosity.VERBOSE, "Server: Ack-Ack message received")
                header = Header.deserialize(message)
                
                if header.ack:
                    return create_stream(new_client_socket, client_address, sequence_number + 1, ack_number, self.method, self.logger)
                
            return None
        except Exception as e:
            raise e

    def bind(self, ip, port):
        self.socket.bind((ip, port))
    
    @classmethod
    def generate_initial_sequence_number(cls):
        return random.randint(0, 2**32 - 1)
