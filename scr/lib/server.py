from socket import *
import threading

from lib.rdtp import RDTP

class Server:
    def __init__(self, ip, port, dir):
        try:    
            self.ip = ip
            self.port = port
            self.dir = dir
        except Exception as e:
            raise e

    def listen(self):
        try:
            rdtp = RDTP()
            connection_with_client = rdtp.accept(self.ip, self.port)
        except Exception as e:
            print(e)
        # if client_address is not None:
        #     threading.Thread(target=self.rdtp.handle_client, args=(client_address)).start()
