from enum import Enum

class ProtocolError(Exception, Enum):
    ERROR_NO_SYNACK = 1

class AplicationError(Exception, Enum):
    ERROR = 1

