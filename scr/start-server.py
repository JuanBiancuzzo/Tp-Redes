from lib.server import Server 

def main():

    server = Server("", 12000, "hola")

    server.listen()

if __name__ == "__main__":
    main()
