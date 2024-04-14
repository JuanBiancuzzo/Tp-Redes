from socket import *

class Server:
    def __init__(self, ip, port, dir):
        self.ip = ip
        self.port = port
        self.dir = dir
        
        self.serverSocket = socket(AF_INET, SOCK_DGRAM)
        self.serverSocket.bind((self.ip, self.port))

        print(self.serverSocket)
        print('El servidor está listo para recibir')

    def listen(self):
        while True:
            message, clientAddress = self.serverSocket.recvfrom(2048)
            modifiedMessage = message.decode().upper()

            print(modifiedMessage)

            self.serverSocket.sendto(modifiedMessage.encode(), clientAddress)
