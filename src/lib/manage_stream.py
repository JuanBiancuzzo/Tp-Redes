from lib.errors import ProtocolError
from lib.rdtp_stream_proxy import RDTPStreamProxy
from lib.rdtp_stream import RDTPStream, TIMEOUT

from lib.parameter import OutputVerbosity
from lib.logger import Logger

import threading

SELF_TIMEOUT = TIMEOUT / 10

def manage_stream(stream: RDTPStream, logger: Logger):
    """
    Exception:
        * ProtocolError.ERROR_EMPTY_MESSAGE
        * ProtocolError.ERROR_PACKING
        * ProtocolError.ERROR_UNPACKING
        * ProtocolError.ERROR_SENDING_MESSAGE
        * ProtocolError.ERROR_RECEIVING_MESSAGE
    """

    while not (stream.sent_close_message and stream.received_close_message):

        # chequea todos los timers de los send message y hace la logica que sea necesaria
        # stream.check_times()
        # Que se tenga un número de timeout repetidos, aprox también con lo de ping pong
        
        segment = stream.recv_segment(SELF_TIMEOUT)
        if segment is not None:
            stream.recv(segment)

        payload = stream.send_payload(SELF_TIMEOUT)
        if payload is not None:
            stream.send(payload)

        if stream.close_queue.full() and stream.window.empty():
            stream.send_fin_message()
            _ = stream.close_queue.get()
        
        # if stream_should_close(stream, segment, payload):
            # stream.close()
    
    logger.log(OutputVerbosity.VERBOSE, "Closing stream")

def stream_should_close(stream, last_segment, last_payload):
    return  (last_payload is None and last_segment is None and stream.received_close_message and not stream.sent_close_message) or \
            (stream.close_queue.full() and not stream.sent_close_message)
        
def create_stream(socket, receiver_address, sequence_number, ack_number, method, logger):

    stream = RDTPStream(socket, receiver_address, sequence_number, ack_number, method, logger)
    received_queue = stream.received_queue
    send_queue = stream.send_queue
    close_queue = stream.close_queue

    stream_manager_handler = threading.Thread(
        target = manage_stream,
        args = [stream, logger]
    )
    
    try:
        stream_manager_handler.start()
    except:
        raise ProtocolError.ERROR_CREATING_STREAM_THREAD        

    return RDTPStreamProxy(received_queue, send_queue, close_queue, stream_manager_handler)