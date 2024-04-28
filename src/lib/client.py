import socket
import os
import struct 

from lib.rdtp import RDTP
from lib.parameter import ActionMethod
from lib.protocol.header_package import HeaderPackage

FORMAT = '>Q' # 8 bytes
FILE_SPLIT = 2**28 # 250 Mbytes 

class Client:
    def __init__(self, method, logger, host, port):
        client = RDTP(method, logger)
        self.stream = client.connect(host, port)

    @classmethod
    def sendInfoPackage(cls, connection, action, filename, filepath, logger):
        infoPackage = HeaderPackage(
                action,
                filename,
                filepath
        )

        connection.send(infoPackage.serialize())

    @classmethod
    def uploadFile(cls, connection, file, fileSize, logger):
        connection.send(struct.pack(FORMAT, fileSize))
        split = min(FILE_SPLIT, fileSize)

        while fileSize > 0:
            message = file.read(split)
            connection.send(message)

            fileSize -= split
            split = min(FILE_SPLIT, fileSize)
    
    def upload(self, filename, filepath):
        fileSize = os.path.getsize(f"{filepath}/{filename}")
        Self.sendInfoPackage(
            self.stream,
            ActionMethod.UPLOAD,
            filename,
            filepath,
            self.logger
        )

        with open(f"{filepath}/{filename}", "rb") as file:
            Self.uploadFile(self.stream, file, fileSize, self.logger)

        self.stream.close()

    def download(self, filename, filepath):
        pass
    
