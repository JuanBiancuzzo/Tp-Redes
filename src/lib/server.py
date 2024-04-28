from socket import *
import struct 

from lib.rdtp import RDTP
from lib.protocol.header_package import HeaderPackage, HEADER_SIZE
from lib.parameter import ActionMethod
from lib.logger import Logger

FILE_SIZE_SIZE = 8
FORMAT = '>Q'

FILE_SPLIT = 2**28 # 250 Mbytes 

class Server:
    def __init__(self, method, logger, ip, port, dir):
        self.ip = ip
        self.port = port
        self.dir = dir

        self.rdtp = RDTP(method, logger)
        self.logger = logger

    def listen(self):
        return self.rdtp.accept(self.ip, self.port)

    @classmethod
    def handleUpload(cls, connection, file, logger):
        message = connection.recv(FILE_SIZE_SIZE)
        fileSize = struct.unpack(FORMAT, message)[0]

        split = min(FILE_SPLIT, fileSize)
        while fileSize > 0:
            message = connection.recv(split)

            file.write(message)

            fileSize -= split
            split = min(FILE_SPLIT, fileSize)

    @classmethod
    def handleDownload(cls, connection, fileName, filePath, logger):
        pass

    def handleClient(self, connection):
        message = connection.recv(HEADER_SIZE)
        action, fileNameSize, filePathSize = HeaderPackage.getSize(message)

        message = connection.recv(fileNameSize + filePathSize)
        package = HeaderPackage.deserialize(message, action, fileNameSize)

        if package.action == ActionMethod.UPLOAD:
            with open(f"{self.dir}/{package.filePath}/{package.fileName}", "wb") as file:
                Self.handleUpload(connection, file, self.logger)
        else:
            Self.handleDownload(connection, package.fileName, package.filePath, self.logger)

        connection.close()
