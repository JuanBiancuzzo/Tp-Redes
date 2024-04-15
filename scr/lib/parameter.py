from dataclasses import dataclass
from enum import Enum

class OutputVerbosity(Enum):
    NORMAL = 1
    VERBOSE = 2
    QUIET = 3

@dataclass
class ClientParameter:
    outputVerbosity: OutputVerbosity
    host: str
    port: str
    filePath: str
    nameFile: str

@dataclass
class ServerParameter:
    outputVerbosity: OutputVerbosity
    host: str
    port: str
    storagePath: str

