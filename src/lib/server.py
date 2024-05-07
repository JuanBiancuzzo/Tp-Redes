import os
import struct

from lib.rdtp import RDTP
from lib.protocol.header_package import HeaderPackage, HEADER_SIZE
from lib.parameter import ActionMethod, OutputVerbosity
from lib.errors import ProtocolError, ApplicationError

FILE_SIZE_SIZE = 8
FORMAT = '>Q'

FILE_SPLIT = 2**28  # 250 Mbytes


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


class Server:
    def __init__(self, method, logger, ip, port, dir):
        self.ip = ip
        self.port = port
        self.dir = dir

        # Creando el directorio
        try:
            os.makedirs(os.path.join(os.getcwd(), dir), exist_ok=True)
        except Exception as e:
            logger.log(
                OutputVerbosity.VERBOSE,
                f"Error creating directory: {e}")

        self.rdtp = RDTP(method, logger)
        self.rdtp.bind(ip, port)
        self.logger = logger

    def listen(self):
        return self.rdtp.accept(self.ip, self.port)

    @classmethod
    def handleUpload(cls, connection, file, logger):
        logger.log(OutputVerbosity.VERBOSE, "Receiving file size")
        try:
            message = connection.recv(FILE_SIZE_SIZE)
        except ProtocolError:
            raise ApplicationError.ERROR_RECEIVING

        fileSize = struct.unpack(FORMAT, message)[0]
        logger.log(
            OutputVerbosity.VERBOSE,
            f"File to save of size: {calculateSizeString(fileSize)}")

        logger.log(OutputVerbosity.NORMAL, "Receiving file from client")
        split = min(FILE_SPLIT, fileSize)
        while fileSize > 0:
            try:
                message = connection.recv(split)
            except ProtocolError:
                raise ApplicationError.ERROR_RECEIVING

            logger.log(
                OutputVerbosity.VERBOSE,
                f"Package of size: {calculateSizeString(split)} received")

            file.write(message)

            fileSize -= split
            split = min(FILE_SPLIT, fileSize)

        logger.log(OutputVerbosity.QUIET, "File received")

    @classmethod
    def handleDownload(cls, connection, file, fileSize, logger):
        logger.log(OutputVerbosity.VERBOSE, "Sending file size")
        try:
            connection.send(struct.pack(FORMAT, fileSize))
        except ProtocolError:
            raise ApplicationError.ERROR_SENDING
        logger.log(OutputVerbosity.VERBOSE, "File size sent")

        split = min(FILE_SPLIT, fileSize)

        logger.log(OutputVerbosity.NORMAL, "Sending file to client")
        while fileSize > 0:
            message = file.read(split)
            try:
                connection.send(message)
            except ProtocolError:
                raise ApplicationError.ERROR_SENDING

            logger.log(OutputVerbosity.VERBOSE,
                       f"Package of size: {calculateSizeString(split)} sent")

            fileSize -= split
            split = min(FILE_SPLIT, fileSize)

        logger.log(OutputVerbosity.QUIET, "File sent")

    def handleClient(self, connection):
        self.logger.log(OutputVerbosity.VERBOSE,
                        "Waiting for package with method settings")

        try:
            message = connection.recv(HEADER_SIZE)
        except ProtocolError:
            raise ApplicationError.ERROR_RECEIVING
        (action, fileNameSize, filePathSize) = HeaderPackage.getSize(message)

        try:
            message = connection.recv(fileNameSize + filePathSize)
        except ProtocolError:
            raise ApplicationError.ERROR_RECEIVING
        package = HeaderPackage.deserialize(message, action, fileNameSize)

        actionName = "upload" if action == ActionMethod.UPLOAD else "download"
        self.logger.log(OutputVerbosity.NORMAL,
                        f"Receiving package of type {actionName}")

        if package.action == ActionMethod.UPLOAD:
            self.logger.log(
                OutputVerbosity.NORMAL,
                f"Receiving file: {package.fileName}\n\
                    \tSaving it at: {package.filePath}")

            # Creando el directorio
            try:
                os.makedirs(
                    os.path.join(
                        os.getcwd(),
                        f"{self.dir}/{package.filePath}"),
                    exist_ok=True)
            except Exception as e:
                self.logger.log(
                    OutputVerbosity.VERBOSE,
                    f"Error creating directory: {e}")

            with open(f"{self.dir}/{package.filePath}/{package.fileName}", "wb") as file:
                Server.handleUpload(connection, file, self.logger)
        else:
            self.logger.log(
                OutputVerbosity.NORMAL,
                f"Sending file: {package.fileName}\n\
                    \tFrom: {package.filePath}")
            fileSize = os.path.getsize(
                f"{self.dir}/{package.filePath}/{package.fileName}")

            with open(f"{self.dir}/{package.filePath}/{package.fileName}", "rb") as file:
                Server.handleDownload(connection, file, fileSize, self.logger)

        self.logger.log(
            OutputVerbosity.NORMAL,
            "Closing connection with client")
        connection.close()
        self.logger.log(OutputVerbosity.QUIET, "Closed connection with client")
