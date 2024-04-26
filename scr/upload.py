import argparse

from lib.parameter import ClientParameter, OutputVerbosity, SendMethod, CustomFormatter
from lib.rdtp import RDTP

def obtainParameters():
    parser = argparse.ArgumentParser(
        prog = "upload", 
        description = "Default description",
        formatter_class=CustomFormatter,
    )

    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "-v", "--verbose", 
        action = "store_const", 
        const = OutputVerbosity.VERBOSE,
        help = "increase output verbosity"
    )
    verbosity.add_argument(
        "-q", "--quite", 
        action = "store_const",
        const = OutputVerbosity.QUIET,
        help = "decrease output verbosity"
    )

    parser.add_argument("-H", "--host", default="", dest="addr", help="server IP address")
    parser.add_argument("-p", "--port", default=123123, dest="port", type=int, help="server port")

    parser.add_argument("-s", "--src", default="", dest="filepath", help="source file path")
    parser.add_argument("-n", "--name", default="", dest="filename", help="name file name")

    method = parser.add_mutually_exclusive_group()
    method.add_argument(
        "-r", "--select-repeat", 
        action = "store_const",
        const = SendMethod.SELECTIVE_REPEAT,
        default = SendMethod.SELECTIVE_REPEAT,
        help = "selective repeat method (default)"
    )
    method.add_argument(
        "-w", "--stop-wait", 
        action = "store_const", 
        const = SendMethod.STOP_WAIT,
        help = "stop and wait method"
    )

    args = parser.parse_args() # Sale completamente 

    outputVerbosity = OutputVerbosity.NORMAL
    if args.verbose is not None:
        outputVerbosity = args.verbose
    elif args.quite is not None:
        outputVerbosity = args.quite

    return ClientParameter(
        outputVerbosity,
        host = args.addr,
        port = args.port,
        filePath = args.filepath,
        nameFile = args.filename,
        method = args.select_repeat if args.stop_wait is None else args.stop_wait
    )

def main(parameter):
    cliente = RDTP(parameter.method)
    stream = cliente.connect("localhost", 8080)

    print(parameter)

if __name__ == "__main__":
    parameter = obtainParameters()
    main(parameter)
