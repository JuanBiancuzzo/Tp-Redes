import struct
from dataclasses import dataclass
from lib.parameter import ActionMethod

FORMAT = '>BII'
HEADER_SIZE = 9
ENCODING = "UTF-8"

@dataclass
class HeaderPackage:
    action: ActionMethod
    fileName: str
    filePath: str

    def serialize(self):
        fileNameSize = len(self.fileName)
        filePathSize = len(self.filePath)

        return struct.pack(
            FORMAT,
            self.action.value,
            fileNameSize,
            filePathSize
        ) + self.fileName.encode(encoding=ENCODING) + self.filePath.encode(encoding=ENCODING) 

    @classmethod
    def getSize(cls, data):
        # Solo se puede guardar los tamaños
        actionValue, fileNameSize, filePathSize = struct.unpack(FORMAT, data)

        action = ActionMethod.UPLOAD
        if actionValue == ActionMethod.DOWNLOAD.value:
            action = ActionMethod.DOWNLOAD

        return action, fileNameSize, filePathSize

    @classmethod
    def deserialize(cls, data, action, fileNameSize):
        fileName = data[:fileNameSize].decode(encoding=ENCODING)
        filePath = data[fileNameSize:].decode(encoding=ENCODING)

        return HeaderPackage(
            action,
            fileName,
            filePath
        )
