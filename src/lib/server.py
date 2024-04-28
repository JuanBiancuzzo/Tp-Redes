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
        logger.log(OutputVerbosity.VERBOSE, "Receiving file size")
        message = connection.recv(FILE_SIZE_SIZE)
        fileSize = struct.unpack(FORMAT, message)[0]

        if fileSize < 2**10:
            fileSizeMessage = f"{split} bytes"
        else if fileSize < 2**20:
            fileSizeMessage = f"{'{:.2f}'.format(split / 2**10)} Kb"
        else if fileSize < 2**30:
            fileSizeMessage = f"{'{:.2f}'.format(split / 2**20)} Mb"
        else:
            fileSizeMessage = f"{'{:.2f}'.format(split / 2**30)} Gb"

        logger.log(OutputVerbosity.VERBOSE, f"File to save of size: {fileSizeMessage}")


        logger.log(OutputVerbosity.NORMAL, "Receiving file from client")
        split = min(FILE_SPLIT, fileSize)
        while fileSize > 0:
            message = connection.recv(split)

            if split < 2**10:
                splitMessage = f"{split} bytes"
            else if split < 2**20:
                splitMessage = f"{'{:.2f}'.format(split / 2**10)} Kb"
            else:
                splitMessage = f"{'{:.2f}'.format(split / 2**20)} Mb"

            logger.log(OutputVerbosity.VERBOSE, f"Package of size: {splitMessage} sent")

            file.write(message)

            fileSize -= split
            split = min(FILE_SPLIT, fileSize)

        logger.log(OutputVerbosity.QUIET, "File received")

    @classmethod
    def handleDownload(cls, connection, fileName, filePath, logger):
        pass

    def handleClient(self, connection):
        self.logger.log(OutputVerbosity.VERBOSE, "Waiting for package with method settings")
        message = connection.recv(HEADER_SIZE)
        action, fileNameSize, filePathSize = HeaderPackage.getSize(message)

        message = connection.recv(HEADER_SIZE)
        message = connection.recv(fileNameSize + filePathSize)
        package = HeaderPackage.deserialize(message, action, fileNameSize)

        actionName = "upload" if action == ActionMethod.UPLOAD else "download"
        self.logger.log(OutputVerbosity.NORMAL, f"Receiving package of type {actionName}")

        if package.action == ActionMethod.UPLOAD:
            self.logger.log(OutputVerbosity.NORMAL, f"Receiving file: {package.fileName}\n\tSaving it at: {package.filePath}")

            with open(f"{self.dir}/{package.filePath}/{package.fileName}", "wb") as file:
                Server.handleUpload(connection, file, self.logger)
        else:
            self.logger.log(OutputVerbosity.NORMAL, f"Sending file: {package.fileName}\n\tFrom: {package.filePath}")

            Server.handleDownload(connection, package.fileName, package.filePath, self.logger)

        self.logger.log(OutputVerbosity.NORMAL, "Closing connection with client")
        connection.close()
        self.logger.log(OutputVerbosity.QUIET, "Closed connection with client")
