import struct
from dataclasses import dataclass
from lib.parameter import ActionMethod
from lib.errors import ProtocolError

FORMAT = '>BII'
HEADER_SIZE = 9
ENCODING = "UTF-8"


@dataclass
class HeaderPackage:
    action: ActionMethod
    fileName: str
    filePath: str

    def serialize(self):
        """
        Exceptions:
            * ProtocolError.ERROR_ENCODING_FILE_DATA
            * ProtocolError.ERROR_PACKING
        """

        fileNameSize = len(self.fileName)
        filePathSize = len(self.filePath)

        try:
            fileNameSerialized = self.fileName.encode(encoding=ENCODING)
            filePathSerialized = self.filePath.encode(encoding=ENCODING)
        except UnicodeEncodeError:
            raise ProtocolError.ERROR_ENCODING_FILE_DATA

        try:
            return struct.pack(
                FORMAT,
                self.action.value,
                fileNameSize,
                filePathSize
            ) + fileNameSerialized + filePathSerialized

        except struct.error:
            raise ProtocolError.ERROR_PACKING

    @classmethod
    def getSize(cls, data):
        """
        Exceptions:
            * ProtocolError.ERROR_UNPACKING
            * ProtocolError.ERROR_INVALID_ACTION
        """

        # Solo se puede guardar los tamaños
        try:
            actionValue, fileNameSize, filePathSize = struct.unpack(
                FORMAT, data)
        except struct.error:
            raise ProtocolError.ERROR_UNPACKING

        if actionValue == ActionMethod.UPLOAD.value:
            action = ActionMethod.UPLOAD
        elif actionValue == ActionMethod.DOWNLOAD.value:
            action = ActionMethod.DOWNLOAD
        else:
            raise ProtocolError.ERROR_INVALID_ACTION

        return action, fileNameSize, filePathSize

    @classmethod
    def deserialize(cls, data, action, fileNameSize):
        """
        Exceptions:
            * ProtocolError.ERROR_DECODING_FILE_DATA
        """

        try:
            fileName = data[:fileNameSize].decode(encoding=ENCODING)
            filePath = data[fileNameSize:].decode(encoding=ENCODING)

        except UnicodeDecodeError:
            raise ProtocolError.ERROR_DECODING_FILE_DATA

        return HeaderPackage(
            action,
            fileName,
            filePath
        )
