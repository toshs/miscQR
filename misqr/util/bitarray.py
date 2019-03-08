
class Bitarray():
    def __init__(self, b=None, length=None, order=1):
        if b == None:
            self.array = [] 
        else:
            self.array = self.bytes_to_bitarray(b, length, order) 

    def __repr__(self):
        return str(self.array)

    def __add__(self, other):
        result = Bitarray()
        result.array = self.array + other.array
        return result

    def bytes_to_bitarray(self, bytes, length, order=1):
        bitarray = [False for _ in range(len(bytes)*8)]
        for i, b in enumerate(bytes):
            if order == 1:
                for j in range(8):
                    bitarray[i * 8 + j] = True if (b >> (7-j) & 1) else False
            else:
                for j in range(8):
                    bitarray[i * 8 + j] = True if (b >> j & 1) else False

        if length == None:
            return bitarray
        else:
            if length > len(bitarray):
                return [False]*(length - len(bitarray)) + bitarray
            else:
                return bitarray[-length:]
    
    def to_bytes_array(self):
        padded_array = self.padding()
        bytes_array = [0 for _ in range(len(padded_array) // 8)]
        for i in range(len(padded_array) // 8):
            for j in range(8):
                if padded_array[i * 8 + j]: bytes_array[i] += 1 << (7-j)
        
        return bytes_array

    def padding(self):
        pad = (8 - len(self.array) % 8) % 8
        return self.array + [False for _ in range(pad)]