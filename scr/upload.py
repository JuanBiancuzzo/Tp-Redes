from socket import *

class Servidor:
    pass

def main():
    serverName = 'localhost'
    serverPort = 12000

    clientSocket = socket(AF_INET, SOCK_DGRAM)

    print(clientSocket)

    message = 'hola tanto tiempo'
    clientSocket.sendto(message.encode(),(serverName, serverPort))
    modifiedMessage, serverAddress = clientSocket.recvfrom(2048)

    print(modifiedMessage.decode())

    clientSocket.close()

if __name__ == "__main__":
    main()
