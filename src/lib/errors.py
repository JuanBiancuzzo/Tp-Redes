from enum import Enum

class ProtocolError(Exception, Enum):
    ERROR_NO_SYNACK = 1
    ERROR_ENCODING_FILE_DATA = 2
    ERROR_DECODING_FILE_DATA = 3
    ERROR_PACKING = 4
    ERROR_UNPACKING = 5
    ERROR_INVALID_ACTION = 6
    ERROR_EMPTY_MESSAGE = 7
    ERROR_SENDING_MESSAGE = 8
    ERROR_RECEIVING_MESSAGE = 9
    ERROR_CREATING_STREAM_THREAD = 10

class AplicationError(Exception, Enum):
    ERROR = 1

