from lib.errors import ProtocolError
from lib.rdtp_stream_proxy import RDTPStreamProxy
from lib.rdtp_stream import RDTPStream, TIMEOUT

import threading

SELF_TIMEOUT = TIMEOUT / 10

def manage_stream(stream: RDTPStream):
    """
    Exception:
        * ProtocolError.ERROR_EMPTY_MESSAGE
        * ProtocolError.ERROR_PACKING
        * ProtocolError.ERROR_UNPACKING
        * ProtocolError.ERROR_SENDING_MESSAGE
        * ProtocolError.ERROR_RECEIVING_MESSAGE
    """
    message_buffer = {}

    while not (stream.sent_close_message and stream.received_close_message):
        
        segment = stream.recv_segment(SELF_TIMEOUT)
        if segment is not None:
            stream.recv(segment, message_buffer)

        payload = stream.send_payload(SELF_TIMEOUT)
        if payload is not None:
            stream.send(payload)
        
        if stream_should_close(stream, segment, payload):
            stream.close()

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
        args = [stream]
    )
    
    try:
        stream_manager_handler.start()
    except:
        raise ProtocolError.ERROR_CREATING_STREAM_THREAD        

    return RDTPStreamProxy(received_queue, send_queue, close_queue, stream_manager_handler)