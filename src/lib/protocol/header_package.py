import struct
from lib.parameter import ActionMethod

FORMAT = '>BII'
HEADER_SIZE = 9

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
        ) + self.fileName.encode(encoding="UTF-8") 
        + self.filePath.encode(encoding="UTF-8") 

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
        fileName = data[:fileNameSize]
        filePath = data[fileNameSize + 1:]

        HeaderPackage(
            action,
            fileName,
            filePath
        )
