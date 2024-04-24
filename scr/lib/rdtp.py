from socket import *
from lib.protocol.header import Header, HEADER_SIZE
import random

SRC_PORT_INDEX = 1

class RDTP:
    def __init__(self, socket, receiver_address, sequence_number, ack_number):
        self.socket = socket
        self.receiver_address = receiver_address
        self.sequence_number = sequence_number
        self.ack_number = ack_number
    
    # Para el cliente
    @classmethod
    def connect(cls, dest_ip, dest_port):
        server_socket = socket(AF_INET, SOCK_DGRAM)
        src_port = server_socket.getsockname()[SRC_PORT_INDEX]
        sequence_number = RDTP.generate_initial_sequence_number()
        syn_message = RDTP.craft_syn_message(src_port, dest_port, sequence_number)
        
        try: 
            
            server_socket.sendto(syn_message.serialize(), (dest_ip, dest_port))
            print("mande el syn")
            
            message, server_address = server_socket.recvfrom(HEADER_SIZE)
            print("recibi el syn-ack")
            
            header = Header.deserialize(message)
            ack_number = header.seq_num + 1
            
            if header.syn and header.ack:
                
                sequence_number += 1
                ack_ack_message = RDTP.craft_ack_ack_message(src_port, dest_port, sequence_number, ack_number)
                server_socket.sendto(ack_ack_message.serialize(), server_address)
                print("mande el ackack")
                
                return RDTP(server_socket, server_address, sequence_number, ack_number)
                
        except Exception as e:
            raise e

    # Para el servidor
    @classmethod
    def accept(cls, ip, port):
        client_socket = socket(AF_INET, SOCK_DGRAM)
        client_socket.bind((ip, port))
        
        try:
            
            message, client_address = client_socket.recvfrom(HEADER_SIZE)
            print("server: recibi el syn")
            header = Header.deserialize(message)
            
            if header.syn:
                
                sequence_number = RDTP.generate_initial_sequence_number()
                ack_number = header.seq_num + 1
                dest_port = client_address[SRC_PORT_INDEX]
                
                syn_ack_message = RDTP.craft_syn_ack_message(port, dest_port, sequence_number, ack_number)
                client_socket.sendto(syn_ack_message.serialize(), client_address)
                print("server: mande el syn-ack")
                
                message, client_address = client_socket.recvfrom(HEADER_SIZE)
                print("server: recibi el ackack")
                header = Header.deserialize(message)
                
                if header.ack:
                    return RDTP(client_socket, client_address, sequence_number, ack_number)
                
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
    
    def get_src_port(self):
        return self.socket.getsockname()[SRC_PORT_INDEX]
    
    @classmethod
    def generate_initial_sequence_number(cls):
        return random.randint(0, 2**32 - 1)