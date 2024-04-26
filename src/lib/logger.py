from lib.parameter import OutputVerbosity

class Logger:
    def __init__(self, verbosity):
        self.verbosity = verbosity

    def log(self, verbosity, message):
        if self.verbosity.value >= verbosity.value:
            print(message)
