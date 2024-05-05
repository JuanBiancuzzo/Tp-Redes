
class RDTPStreamProxy:

    def __init__(self, received_queue, send_queue, close_queue, stream_manager_handler):
        self.send_queue = send_queue
        self.received_queue = received_queue
        self.close_queue = close_queue
        
        self.stream_manager_handler = stream_manager_handler
        
        self.incomplete_received = None

    def send(self, message: bytes):
        self.send_queue.put(message)

    def recv(self, size: int):
        message = bytearray()

        if self.incomplete_received is not None:
            length_incomplete_received = len(self.incomplete_received)
            size_of_read = min(size, length_incomplete_received)

            message += self.incomplete_received[:size_of_read]
            size -= size_of_read

            if length_incomplete_received > size_of_read:
                self.incomplete_received = self.incomplete_received[size_of_read:]
            else:
                self.incomplete_received = None

        while size > 0:
            received_message = self.received_queue.get()

            length_received = len(received_message)
            size_of_read = min(size, length_received)

            message += received_message[:size_of_read]
            size -= size_of_read

            if length_received > size_of_read:
                self.incomplete_received = received_message[size_of_read:]

            self.received_queue.task_done()

        return bytes(message)

    def close(self):
        self.close_queue.put("CLOSE")
        self.stream_manager_handler.join()