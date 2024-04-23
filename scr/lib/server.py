from socket import *
import threading

from lib.rdtp import RDTP

class Server:
    def __init__(self, ip, port, dir):
        try:    
            self.ip = ip
            self.port = port
            self.dir = dir
            self.rdtp = RDTP()
            self.rdtp.bind(ip, port)
        except Exception as e:
            raise e

    def listen(self):
        while True:
            try:
                client_address = self.rdtp.accept()
            except Exception as e:
                print(e)
            # if client_address is not None:
            #     threading.Thread(target=self.rdtp.handle_client, args=(client_address)).start()
