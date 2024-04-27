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
    
    def upload(self, filename, filepath):
        infoPackage = HeaderPackage(
                ActionMethod.UPLOAD,
                filename,
                filepath
        )

        self.stream.send(infoPackage.serialize())

        fileSize = os.path.getsize(f"{filePath}/{fileName}")
        self.stream.send(struct.pack(FORMAT, fileSize))

        with open(f"{filePath}/{fileName}", "rb") as file:
            split = min(FILE_SPLIT, fileSize)

            while fileSize > 0:
                message = file.read(split)
                self.stream.send(message)

                fileSize -= split
                split = min(FILE_SPLIT, fileSize)

        self.stream.close()

    def download(self, filename, filepath):
        pass
    
