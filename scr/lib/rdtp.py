from socket import *
from lib.protocol.header import Header, HEADER_SIZE
import random

SRC_PORT_INDEX = 1

class RDTP:
    def __init__(self):
        self.socket = socket(AF_INET, SOCK_DGRAM)
        
    def bind(self, ip, port):
        self.socket.bind((ip, port))
    
    # Para el cliente
    def connect(self, dest_ip, dest_port):
        try: 
            syn_message = self.craft_syn_message(dest_port)
            self.socket.sendto(syn_message.serialize(), (dest_ip, dest_port))
            print("mande el syn")
            message, server_address = self.socket.recvfrom(HEADER_SIZE)
            print("recibi el syn-ack")
            header = Header.deserialize(message)
            if header.syn and header.ack:
                ack_ack_message = self.craft_ack_ack_message(header)
                self.socket.sendto(ack_ack_message.serialize(), server_address)
                print("mande el ackack")
        except Exception as e:
            raise e

    # Para el servidor
    def accept(self):
        try:
            message, client_address = self.socket.recvfrom(HEADER_SIZE)
            print("server: recibi el syn")
            header = Header.deserialize(message)
            if header.syn:
                syn_ack_message = self.craft_syn_ack_message(header)
                self.socket.sendto(syn_ack_message.serialize(), client_address)
                print("server: mande el syn-ack")
                message, client_address = self.socket.recvfrom(HEADER_SIZE)
                print("server: recibi el ackack")
                header = Header.deserialize(message)
                if header.ack:
                    return client_address
            return None
        except Exception as e:
            raise e
    
    def craft_syn_message(self, dest_port):
        src_port = self.get_src_port()
        sequence_number = self.generate_initial_sequence_number()
        return Header(src_port, dest_port, sequence_number, 0, 0, True, False, False, False)
    
    def craft_syn_ack_message(self, received_header):
        sequence_number = self.generate_initial_sequence_number()
        return Header(received_header.dst_port, received_header.src_port, sequence_number, received_header.seq_num + 1, 0, True, True, False, False)
    
    def craft_ack_ack_message(self, received_header):
        return Header(received_header.dst_port, received_header.src_port, received_header.ack_num + 1, received_header.seq_num + 1, 0, False, True, False, False)
    
    def get_src_port(self):
        return self.socket.getsockname()[SRC_PORT_INDEX]
    
    def generate_initial_sequence_number(self):
        return random.randint(0, 2**32 - 1)