from lib.parameter import OutputVerbosity

class Logger:
    def __init__(self, verbosity: OutputVerbosity):
        self.verbosity = verbosity

    def log(self, verbosity: OutputVerbosity, message: str):
        if self.verbosity.value >= verbosity.value:
            print(message)
