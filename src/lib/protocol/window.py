from collections import deque

class Window:
    def __init__(self, size: int):
        self.size = size
        self.window = deque()
        
    def __len__(self):
        return len(self.window)
        
    def __iter__(self):
        return iter(self.window)
        
    def add_segment(self, segment):
        self.window.append(segment)
    
    # Si el tamaño no cambia me mandaron un ack de uno que ya me ackearon, por lo que se perdió el siguiente.
    def remove_acked_segments(self, ack_number):
        while len(self.window) > 0 and self.window[0].header.seq_num < ack_number:
            self.window.popleft()

    def is_full(self):
        return len(self.window) >= self.size

    def get_oldest_segment(self):
        return self.window[0] if len(self.window) > 0 else None