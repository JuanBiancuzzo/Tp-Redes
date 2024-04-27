import socket

from lib.rdtp import RDTP

class Client:
    def __init__(self, metodo, logger, host, port):
        client = RDTP(metodo, logger)
        self.stream = client.connect(host, port)
    
    def upload(self, filename, filepath):
        pass

    def download(self, filename, filepath):
        pass
    
