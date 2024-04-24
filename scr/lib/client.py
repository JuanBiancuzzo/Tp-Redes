import socket

from lib.rdtp import RDTP

class Client:
    def __init__(self, host, port):
        try: 
            self.host = host
            self.port = port
            self.rdtp = RDTP()
            self.rdtp.connect(host, port)
            print("conexion ok")
        except Exception as e:
            raise e
    
    def download(self, filename, filepath):
        try:
            print("Downloading file")
        except Exception as e:
            raise e
    
    def upload(self, filename, filepath):
        return