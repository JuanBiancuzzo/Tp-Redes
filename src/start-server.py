import argparse
import threading
from lib.server import Server

from lib.parameter import ServerParameter, OutputVerbosity, SendMethod, CustomFormatter
from lib.logger import Logger
from lib.errors import ProtocolError

def obtainParameters():
    parser = argparse.ArgumentParser(
        prog = "start-server", 
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
        "-q", "--quiet", 
        action = "store_const",
        const = OutputVerbosity.QUIET,
        help = "decrease output verbosity"
    )

    parser.add_argument("-H", "--host", default="localhost", dest="addr", help="server IP address")
    parser.add_argument("-p", "--port", default=1234, dest="port", type=int, help="server port")
    parser.add_argument("-s", "--storage", default=".", dest="dirpath", help="storage dir path")

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
    elif args.quiet is not None:
        outputVerbosity = args.quiet

    return ServerParameter(
        outputVerbosity,
        host = args.addr,
        port = args.port,
        storagePath = args.dirpath,
        method = args.select_repeat if args.stop_wait is None else args.stop_wait
    )

def handleClient(server, connection):
    server.handleClient(connection)                

def main(parameter):
    logger = Logger(parameter.outputVerbosity)
    logger.log(OutputVerbosity.VERBOSE, "Initializing server")

    server = Server(
        parameter.method,
        logger,
        parameter.host, 
        parameter.port, 
        parameter.storagePath
    )

    logger.log(OutputVerbosity.QUIET, "Listening for connections")
    handlers = []

    try:
        while True:
            try:
                new_connection = server.listen()
            except ProtocolError as protocolError:
                if protocolError == ProtocolError.ERROR_HANDSHAKE:
                    continue
                else:
                    raise protocolError
            
            client_handler_handle = threading.Thread(
                target = handleClient,
                args = (server, new_connection)
            )
            
            client_handler_handle.start()
            handlers.append(client_handler_handle)
            logger.log(OutputVerbosity.NORMAL, "New connection established")

    except KeyboardInterrupt:
        logger.log(OutputVerbosity.NORMAL, "\nServer stopped. Closing connections")
        for handle in handlers:
            handle.join()

if __name__ == "__main__":
    parameter = obtainParameters()
    main(parameter)
