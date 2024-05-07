import threading
import time
from multiprocessing import Pipe

from lib.errors import ProtocolError
from lib.rdtp_stream_proxy import RDTPStreamProxy
from lib.rdtp_stream import RDTPStream
from lib.protocol.window import TIMEOUT

from lib.parameter import OutputVerbosity
from lib.logger import Logger

SELF_TIMEOUT = TIMEOUT / 50
PING_TIME = TIMEOUT * 10

def manage_stream(stream: RDTPStream, logger: Logger):
    """
    Exception:
        * ProtocolError.ERROR_EMPTY_MESSAGE
        * ProtocolError.ERROR_PACKING
        * ProtocolError.ERROR_UNPACKING
        * ProtocolError.ERROR_SENDING_MESSAGE
        * ProtocolError.ERROR_RECEIVING_MESSAGE
    """
    ping_time_ns = time.time_ns()

    while not (stream.sent_close_message and stream.received_close_message):

        segment = stream.recv_segment(SELF_TIMEOUT)
        if segment is not None:
            stream.recv(segment)

        # chequea todos los timers de los send message y hace la logica que sea necesaria
        # Que se tenga un número de timeout repetidos
        current_time_ns = time.time_ns()
        try:
            if segment is None:
                stream.check_times(current_time_ns)
        except ProtocolError as protocolError:
            if protocolError == ProtocolError.ERROR_RECEIVING_END_DEAD:
                logger.log(OutputVerbosity.QUIET, "Connection dead")
                break
            else:
                raise protocolError
        
        if current_time_ns - ping_time_ns > PING_TIME * 10**9:
            stream.send_ping_message()
            ping_time_ns = current_time_ns

        payload = stream.send_payload(SELF_TIMEOUT)
        if payload is not None:
            stream.send(payload)

        if stream.close_queue.full() and stream.window.empty():
            stream.send_fin_message()
            _ = stream.close_queue.get()
    
    logger.log(OutputVerbosity.VERBOSE, "Closing stream")

    stream.received_pipe.close()
    stream.send_pipe.close()
        
def create_stream(socket, receiver_address, sequence_number, ack_number, method, logger):

    parent_recv_pipe, child_recv_pipe = Pipe(False)
    parent_send_pipe, child_send_pipe = Pipe(False)

    stream = RDTPStream(socket, receiver_address, sequence_number, ack_number, child_recv_pipe, parent_send_pipe,  method, logger)
    close_queue = stream.close_queue

    stream_manager_handler = threading.Thread(
        target = manage_stream,
        args = [stream, logger]
    )
    
    try:
        stream_manager_handler.start()
    except:
        raise ProtocolError.ERROR_CREATING_STREAM_THREAD        

    return RDTPStreamProxy(parent_recv_pipe, child_send_pipe, close_queue, stream_manager_handler)