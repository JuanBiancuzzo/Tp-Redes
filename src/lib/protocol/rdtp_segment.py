from header import Header, HEADER_SIZE

class RDTPSegment:
    def __init__(self, header, bytes):
        self.header = header
        self.bytes = bytes
    
    def serialize(self):
        return self.header.serialize() + self.bytes

    @classmethod
    def deserialize(cls, data):
        header = Header.deserialize(data[:HEADER_SIZE])
        return cls(header, data[HEADER_SIZE:])
    
    @classmethod
    def create_new_message(cls, src_port, dst_port, seq_num, ack_num, bytes):
        header = Header(src_port, dst_port, seq_num, ack_num, len(bytes), False, True, False, False)
        return cls(header, bytes)