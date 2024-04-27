import argparse
from dataclasses import dataclass
from enum import Enum

class OutputVerbosity(Enum):
    QUIET = 1
    NORMAL = 2
    VERBOSE = 3

class SendMethod(Enum):
    STOP_WAIT = 1
    SELECTIVE_REPEAT = 2

class ActionMethod(Enum):
    UPLOAD = 0
    DOWNLOAD = 1

@dataclass
class ClientParameter:
    outputVerbosity: OutputVerbosity
    host: str
    port: int
    filePath: str
    fileName: str
    method: SendMethod

@dataclass
class ServerParameter:
    outputVerbosity: OutputVerbosity
    host: str
    port: int
    storagePath: str
    method: SendMethod

class CustomFormatter(argparse.HelpFormatter):
    def _format_action_invocation(self, action):
        if action.option_strings:
            parts = []
            for option_string in action.option_strings:
                parts.append(option_string)
            return ', '.join(parts)
        else:
            return super()._format_action_invocation(action)

