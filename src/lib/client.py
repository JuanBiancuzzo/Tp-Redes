import socket
import os
import struct 

from lib.rdtp import RDTP
from lib.parameter import ActionMethod
from lib.protocol.header_package import HeaderPackage
from lib.parameter import OutputVerbosity

FORMAT = '>Q' # 8 bytes
FILE_SPLIT = 2**28 # 250 Mbytes 

class Client:
    def __init__(self, method, logger, host, port):
        client = RDTP(method, logger)
        self.stream = client.connect(host, port)
        self.logger = logger

    @classmethod
    def sendInfoPackage(cls, connection, action, filename, filepath, logger):
        logger.log(OutputVerbosity.VERBOSE, "Crafting package with upload settings")
        infoPackage = HeaderPackage(
                action,
                filename,
                filepath
        )

        logger.log(OutputVerbosity.VERBOSE, "Sending package with upload settings")
        connection.send(infoPackage.serialize())
        logger.log(OutputVerbosity.NORMAL, "Package with upload settings sent")

    @classmethod
    def uploadFile(cls, connection, file, fileSize, logger):
        logger.log(OutputVerbosity.VERBOSE, "Sending file size")
        connection.send(struct.pack(FORMAT, fileSize))
        logger.log(OutputVerbosity.VERBOSE, "File size sent")

        split = min(FILE_SPLIT, fileSize)

        logger.log(OutputVerbosity.NORMAL, "Uploading file to server")
        while fileSize > 0:
            message = file.read(split)
            connection.send(message)

            if split < 2**10:
                splitMessage = f"{split} bytes"
            else if split < 2**20:
                splitMessage = f"{'{:.2f}'.format(split / 2**10)} Kb"
            else:
                splitMessage = f"{'{:.2f}'.format(split / 2**20)} Mb"

            logger.log(OutputVerbosity.VERBOSE, f"Package of size: {splitMessage} sent")

            fileSize -= split
            split = min(FILE_SPLIT, fileSize)

        logger.log(OutputVerbosity.QUIET, "File sent")
    
    def upload(self, filename, filepath):
        Client.sendInfoPackage(
            self.stream,
            ActionMethod.UPLOAD,
            filename,
            filepath,
            self.logger
        )

        self.logger.log(OutputVerbosity.NORMAL, f"Sending file: {filename}\n\tFrom: {filepath}")

        fileSize = os.path.getsize(f"{filepath}/{filename}")
        with open(f"{filepath}/{filename}", "rb") as file:
            Client.uploadFile(self.stream, file, fileSize, self.logger)


        self.logger.log(OutputVerbosity.NORMAL, "Closing connection with server")
        self.stream.close()
        self.logger.log(OutputVerbosity.QUIET, "Closed connection with server")

    def download(self, filename, filepath):
        pass
    
