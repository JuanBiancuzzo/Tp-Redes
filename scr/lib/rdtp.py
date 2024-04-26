from socket import *
from lib.protocol.header import Header, HEADER_SIZE
from lib.logger import Logger
from lib.parameter import OutputVerbosity
from lib.rdtp_stream import RDTPStream
import random

SRC_PORT_INDEX = 1

class RDTP:
    def __init__(self, method, logger):
        self.socket = socket(AF_INET, SOCK_DGRAM)

        self.method = method
        self.logger = logger
    
    # Para el cliente
    def connect(self, dest_ip, dest_port):
        src_port = self.socket.getsockname()[SRC_PORT_INDEX]
        sequence_number = RDTP.generate_initial_sequence_number()
        syn_message = RDTP.craft_syn_message(src_port, dest_port, sequence_number)
        
        try: 
            
            self.socket.sendto(syn_message.serialize(), (dest_ip, dest_port))
            self.logger.log(OutputVerbosity.VERBOSE, f"mande el syn a {dest_ip}:{dest_port}")
            
            message, server_address = self.socket.recvfrom(HEADER_SIZE)
            self.logger.log(OutputVerbosity.VERBOSE, "recibi el syn-ack")
            
            header = Header.deserialize(message)
            ack_number = header.seq_num + 1

            # Reescribiendo para nuevo puerto
            server_address = (dest_ip, header.src_port)
            dest_port = header.src_port
            
            if header.syn and header.ack:
                
                sequence_number += 1
                ack_ack_message = RDTP.craft_ack_ack_message(src_port, dest_port, sequence_number, ack_number)
                self.socket.sendto(ack_ack_message.serialize(), server_address)
                self.logger.log(OutputVerbosity.VERBOSE, "mande el ackack")
                
                self.logger.log(OutputVerbosity.QUIET, "hola")
                return RDTPStream(self.socket, server_address, sequence_number, ack_number, self.method, self.logger)
                
        except Exception as e:
            raise e

    # Para el servidor
    def accept(self, ip, port):
        self.socket.bind((ip, port))
        
        try:
            
            message, client_address = self.socket.recvfrom(HEADER_SIZE)
            self.logger.log(OutputVerbosity.VERBOSE, "server: recibi el syn")
            header = Header.deserialize(message)
            
            if header.syn:
                
                sequence_number = RDTP.generate_initial_sequence_number()
                ack_number = header.seq_num + 1
                dest_port = client_address[SRC_PORT_INDEX]

                new_client_socket = socket(AF_INET, SOCK_DGRAM)
                new_client_socket.bind((ip, 0))
                new_port = new_client_socket.getsockname()[SRC_PORT_INDEX]
                
                syn_ack_message = RDTP.craft_syn_ack_message(new_port, dest_port, sequence_number, ack_number)
                self.socket.sendto(syn_ack_message.serialize(), client_address)
                self.logger.log(OutputVerbosity.VERBOSE, "server: mande el syn-ack")
                
                message, client_address = new_client_socket.recvfrom(HEADER_SIZE)
                self.logger.log(OutputVerbosity.VERBOSE, "server: recibi el ackack")
                header = Header.deserialize(message)
                
                if header.ack:
                    return RDTPStream(new_client_socket, client_address, sequence_number, ack_number, self.method, self.logger)
                
            return None
        except Exception as e:
            raise e
    
    @classmethod
    def craft_syn_message(cls, src_port, dest_port, sequence_number):
        return Header(src_port, dest_port, sequence_number, 0, 0, True, False, False, False)
    
    @classmethod 
    def craft_syn_ack_message(cls, src_port, dest_port, sequence_number, ack_number):
        return Header(src_port, dest_port, sequence_number, ack_number, 0, True, True, False, False)
    
    @classmethod
    def craft_ack_ack_message(cls, src_port, dest_port, sequence_number, ack_number):
        return Header(src_port, dest_port, sequence_number, ack_number, 0, False, True, False, False)
    
    @classmethod
    def generate_initial_sequence_number(cls):
        return random.randint(0, 2**32 - 1)
