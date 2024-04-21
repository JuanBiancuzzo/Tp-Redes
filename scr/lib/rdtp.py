from socket import *
from scr.lib.protocol.header import Header
import random

SRC_PORT_INDEX = 1

class RDTP:
    def __init__(self):
        self.socket = socket(AF_INET, SOCK_DGRAM)
        
    def bind(self, ip, port):
        self.socket.bind((ip, port))
        
    def connect(self, dest_ip, dest_port):
        serialized_syn_message = self.craft_syn_message(dest_port)
        self.socket.sendto(serialized_syn_message, (dest_ip, dest_port))
    
    def craft_syn_message(self, dest_port):
        src_port = self.get_src_port()
        sequence_number = self.generate_initial_squence_number()
        syn_header = Header(src_port, dest_port, sequence_number, 0, 0, True, False, False, False)
        return syn_header.serialize()
        
    def get_src_port(self):
        return self.socket.getsockname()[SRC_PORT_INDEX]
    
    def generate_initial_squence_number(self):
        return random.randint(0, 2**32 - 1)