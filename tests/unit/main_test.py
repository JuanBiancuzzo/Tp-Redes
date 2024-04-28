import unittest

import os
import sys

import struct

sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'src')
))

from lib.server import Server, FILE_SPLIT
from lib.client import Client
from lib.protocol.header_package import HeaderPackage, HEADER_SIZE
from lib.parameter import ActionMethod

class MockConnection:
    def __init__(self, content=b""):
        self.contentToSend = content
        self.contentRecv = b""


    def send(self, message):
        self.contentRecv += message

    def recv(self, size):
        content = self.contentToSend[:size]
        self.contentToSend = self.contentToSend[size:]
        return content

class MockFile:
    def __init__(self, content=b""):
        self.contentToSend = content
        self.contentRecv = b""
        self.writeCount = 0

    def write(self, message):
        self.contentRecv += message
        self.writeCount += 1

    def read(self, size):
        content = self.contentToSend[:size]
        self.contentToSend = self.contentToSend[size:]
        return content

class MockLogger:
    def __init__(self):
        pass

    def log(self, verbosity, message):
        pass

class TestUpload(unittest.TestCase):

    def test01EmptyFileServer(self):
        connection = MockConnection(struct.pack('>Q', 0))
        file = MockFile()
        logger = MockLogger()

        Server.handleUpload(connection, file, logger)

        self.assertEqual(file.contentRecv, b"")

    def test02ShortFileServer(self):
        fileString = b"hola tanto tiempo"
        connection = MockConnection(struct.pack('>Q', len(fileString)) + fileString)
        file = MockFile()
        logger = MockLogger()

        Server.handleUpload(connection, file, logger)

        self.assertEqual(file.contentRecv, fileString)

    def test03LongFileServer(self):
        fileString = b"hola tanto tiempo"

        while len(fileString) < FILE_SPLIT:
            fileString += fileString

        connection = MockConnection(struct.pack('>Q', len(fileString)) + fileString)
        file = MockFile()
        logger = MockLogger()

        Server.handleUpload(connection, file, logger)

        self.assertEqual(file.contentRecv, fileString)
        self.assertTrue(file.writeCount > 1)

    def test04EmptyFileClient(self):
        connection = MockConnection()
        file = MockFile()
        logger = MockLogger()

        Client.uploadFile(connection, file, 0, logger)

        self.assertEqual(connection.contentRecv, struct.pack('>Q', 0))

    def test05ShortFileClient(self):
        fileString = b"hola tanto tiempo"

        connection = MockConnection()
        file = MockFile(fileString)
        logger = MockLogger()

        Client.uploadFile(connection, file, len(fileString), logger)

        self.assertEqual(connection.contentRecv, struct.pack('>Q', len(fileString)) + fileString)

    def test06LongFileClient(self):
        fileString = b"hola tanto tiempo"

        while len(fileString) < FILE_SPLIT:
            fileString += fileString

        connection = MockConnection()
        file = MockFile(fileString)
        logger = MockLogger()

        Client.uploadFile(connection, file, len(fileString), logger)

        self.assertEqual(connection.contentRecv, struct.pack('>Q', len(fileString)) + fileString)

    def test07InfoPackageClient(self):
        connection = MockConnection()
        logger = MockLogger()

        action = ActionMethod.UPLOAD
        filename = "pepito"
        filepath = "casa/a"

        Client.sendInfoPackage(connection, action, filename, filepath, logger)

        header = connection.contentRecv[:HEADER_SIZE]

        (actionRecv, fileNameSize, filePathSize) = HeaderPackage.getSize(header)

        self.assertEqual(actionRecv.value, action.value)
        self.assertEqual(len(filename), fileNameSize)
        self.assertEqual(len(filepath), filePathSize)
        
        data = connection.contentRecv[HEADER_SIZE:]

        infoPackage = HeaderPackage.deserialize(data, action, fileNameSize)

        self.assertEqual(infoPackage.fileName, filename.encode(encoding="UTF-8"))
        self.assertEqual(infoPackage.filePath, filepath.encode(encoding="UTF-8"))

if __name__ == '__main__':
    unittest.main()
