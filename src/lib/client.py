import socket
import os
import struct 

from lib.rdtp import RDTP
from lib.parameter import ActionMethod, OutputVerbosity
from lib.protocol.header_package import HeaderPackage
from lib.errors import ProtocolError, AplicationError

FILE_SIZE_SIZE = 8

FORMAT = '>Q' # 8 bytes
# FILE_SPLIT = 2**28 # 250 Mbytes 
FILE_SPLIT = 2**58

def calculateSizeString(numBytes):
    if numBytes < 2**10:
        string = f"{numBytes} bytes"
    elif numBytes < 2**20:
        string = f"{'{:.2f}'.format(numBytes / 2**10)} Kb"
    elif numBytes < 2**30:
        string = f"{'{:.2f}'.format(numBytes / 2**20)} Mb"
    else:
        string = f"{'{:.2f}'.format(numBytes / 2**30)} Gb"

    return string

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

            logger.log(OutputVerbosity.VERBOSE, f"Package of size: {calculateSizeString(split)} sent")

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

    @classmethod
    def downloadFile(cls, connection, file, logger):
        logger.log(OutputVerbosity.VERBOSE, "Receiving file size")
        message = connection.recv(FILE_SIZE_SIZE)
        fileSize = struct.unpack(FORMAT, message)[0]

        logger.log(OutputVerbosity.VERBOSE, f"File to save of size: {calculateSizeString(fileSize)}")

        logger.log(OutputVerbosity.NORMAL, "Receiving file from server")
        split = min(FILE_SPLIT, fileSize)
        while fileSize > 0:
            message = connection.recv(split)

            logger.log(OutputVerbosity.VERBOSE, f"Package of size: {calculateSizeString(split)} received")

            file.write(message)

            fileSize -= split
            split = min(FILE_SPLIT, fileSize)

        logger.log(OutputVerbosity.QUIET, "File downloaded")

    def download(self, filename, filepath):
        Client.sendInfoPackage(
            self.stream,
            ActionMethod.DOWNLOAD,
            filename,
            filepath,
            self.logger
        )

        self.logger.log(OutputVerbosity.NORMAL, f"Receiving file: {filename}\n\tFrom: {filepath}")

        # Creando el directorio
        try:
            os.makedirs(os.path.join(os.getcwd(), filepath), exist_ok=True)
        except:
            pass

        with open(f"{filepath}/{filename}", "wb") as file:
            Client.downloadFile(self.stream, file, self.logger)


        self.logger.log(OutputVerbosity.NORMAL, "Closing connection with server")
        self.stream.close()
        self.logger.log(OutputVerbosity.QUIET, "Closed connection with server")
    
