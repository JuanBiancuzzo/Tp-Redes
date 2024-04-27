class Window:
    def __init__(self, size: int):
        self.size = size
        self.window = []
        
    def __len__(self):
        return len(self.window)
        
    def __iter__(self):
        return iter(self.window)
        
    def add_segment(self, segment):
        self.window.append(segment)
    
    # Si el tamaño no cambia me mandaron un ack de uno que ya me ackearon, por lo que se perdió el siguiente.
    def remove_acked_segments(self, ack_number):
        self.window = [segment for segment in self.window if segment.sequence_number >= ack_number]
    
    def is_full(self):
        return len(self.window) == self.size