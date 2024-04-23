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
            serialized_syn_message = self.craft_syn_message(dest_port)
            self.socket.sendto(serialized_syn_message, (dest_ip, dest_port))
            print("mande el syn")
            message, server_address = self.socket.recvfrom(HEADER_SIZE)
            print("recibi el syn-ack")
            header = Header.deserialize(message)
            if header.syn and header.ack:
                self.socket.sendto(Header(header.dst_port, header.src_port, header.seq_num + 1, 1, 0, 0b0100).serialize(), server_address)
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
                self.socket.sendto(Header(header.dst_port, header.src_port, header.seq_num + 1, header.seq_num + 1, 0, 0b1100).serialize(), client_address)
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
        syn_header = Header(src_port, dest_port, sequence_number, 0, 0, 0b1000)
        return syn_header.serialize()
        
    def get_src_port(self):
        return self.socket.getsockname()[SRC_PORT_INDEX]
    
    def generate_initial_sequence_number(self):
        return random.randint(0, 2**32 - 1)