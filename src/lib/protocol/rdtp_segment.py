from lib.protocol.header import Header, HEADER_SIZE

class RDTPSegment:
    def __init__(self, header: Header, bytes):
        self.header = header
        self.bytes = bytes
    
    def serialize(self):
        """
        Exception:  
            * ProtocolError.ERROR_PACKING
        """

        return self.header.serialize() + self.bytes

    @classmethod
    def deserialize(cls, data):
        """
        Exception:
            * ProtocolError.ERROR_UNPACKING
        """

        header = Header.deserialize(data[:HEADER_SIZE])
        return cls(header, data[HEADER_SIZE:])
    
    @classmethod
    def create_new_message(cls, src_port, dst_port, seq_num, ack_num, bytes):
        header = Header(src_port, dst_port, seq_num, ack_num, len(bytes), False, False, False)
        return cls(header, bytes)
    
    @classmethod
    def create_ack_message(cls, src_port, dst_port, seq_num, ack_num):
        header = Header(src_port, dst_port, seq_num, ack_num, 0, False, True, False)
        return RDTPSegment(header, b"")
    
    @classmethod
    def create_syn_message(cls, src_port, dest_port, sequence_number):
        header =  Header(src_port, dest_port, sequence_number, 0, 0, True, False, False)
        return RDTPSegment(header, b"")
    
    @classmethod
    def create_syn_ack_message(cls, src_port, dest_port, sequence_number, ack_number):
        header = Header(src_port, dest_port, sequence_number, ack_number, 0, True, True, False)
        return RDTPSegment(header, b"")
    
    @classmethod
    def create_ack_ack_message(cls, src_port, dest_port, sequence_number, ack_number):
        header = Header(src_port, dest_port, sequence_number, ack_number, 0, False, True, False)
        return RDTPSegment(header, b"")
    
    @classmethod
    def create_fin_message(cls, src_port, dest_port, sequence_number, ack_number):
        header = Header(src_port, dest_port, sequence_number, ack_number, 0, False, False, True)
        return RDTPSegment(header, b"")
    
    @classmethod
    def create_fin_ack_message(cls, src_port, dest_port, sequence_number, ack_number):
        header = Header(src_port, dest_port, sequence_number, ack_number, 0, False, True, True)
        return RDTPSegment(header, b"")