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
    def create_new_message(cls, src_port, dst_port, seq_num, ack_num, is_last, bytes):
        header = Header(src_port, dst_port, seq_num, ack_num, len(bytes), False, True, False, is_last)
        return cls(header, bytes)
    
    @classmethod
    def create_ack_message(cls, src_port, dst_port, seq_num, ack_num):
        header = Header(src_port, dst_port, seq_num, ack_num, 0, False, True, False, False)
        return RDTPSegment(header, b"")