import unittest

import os
import sys

import struct

sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'src')
))

from lib.server import Server, FILE_SPLIT

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

    def test01EmptyFile(self):
        connection = MockConnection(struct.pack('>Q', 0))
        file = MockFile()
        logger = MockLogger()

        Server.handleUpload(connection, file, logger)

        self.assertEqual(file.contentRecv, b"")

    def test02ShortFile(self):
        fileString = b"hola tanto tiempo"
        connection = MockConnection(struct.pack('>Q', len(fileString)) + fileString)
        file = MockFile()
        logger = MockLogger()

        Server.handleUpload(connection, file, logger)

        self.assertEqual(file.contentRecv, fileString)

    def test03LongFile(self):
        fileString = b"hola tanto tiempo"

        while len(fileString) < FILE_SPLIT:
            fileString += fileString

        connection = MockConnection(struct.pack('>Q', len(fileString)) + fileString)
        file = MockFile()
        logger = MockLogger()

        Server.handleUpload(connection, file, logger)

        self.assertEqual(file.contentRecv, fileString)
        self.assertTrue(file.writeCount > 1)

if __name__ == '__main__':
    unittest.main()
