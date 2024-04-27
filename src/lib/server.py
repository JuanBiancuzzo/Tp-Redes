from socket import *

from lib.rdtp import RDTP

class Server:
    def __init__(self, method, logger, ip, port, dir):
        self.ip = ip
        self.port = port
        self.dir = dir

        self.rdtp = RDTP(method, logger)
        self.logger = logger

    def listen(self):
        return self.rdtp.accept(self.ip, self.port)

    def handleClient(self, connection):
        pass
