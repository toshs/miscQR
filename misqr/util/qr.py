from .block import Block
from .bitarray import Bitarray
from .table import PATTERN_POSITION_TABLE
from .bch import gf_poly_div, G15, G18
from PIL import Image, ImageColor
import reedsolo
import numpy


# Only Support Simgle Encoding Mode
class QR():
    ERROR_CORRECT_L = 0
    ERROR_CORRECT_M = 1
    ERROR_CORRECT_Q = 2
    ERROR_CORRECT_H = 3

    def __init__(self, data, version, error_correct_level, mask_pattern=0b000, color="#000000"):
        self.data = data
        self.version = version
        self.error_correct_level = error_correct_level

        self.mode = self.data_analiyze(self.data)
        self.color = color

        self.encoded_bit_array = self.data_encode(self.data)
        self.encoded_byte_array = self.encoded_bit_array.to_bytes_array()

        block_length, code_length, data_code_length, blocks_info = Block.get_block_info(self.version, self.error_correct_level)
        self.data_code = self.weed_padding(self.encoded_byte_array, data_code_length)
        self.data_blocks = Block.divide_into_block(self.encoded_byte_array, self.version, self.error_correct_level)

        error_code_length = (code_length - data_code_length) // block_length
        self.error_blocks = [block.calculate_error_correction_code(error_code_length) for block in self.data_blocks]

        self.processed_data_code = Block.integrate([block.code for block in self.data_blocks]).code
        self.processed_error_code = Block.integrate(self.error_blocks).code
        self.processed_code = self.processed_data_code + self.processed_error_code

        # For test, mask pattern is fixed
        self.mask_pattern = mask_pattern

        self.matrix = self.make_matrix(Bitarray(self.processed_code).array)

        self.masked_matrix = self.mask(self.mask_pattern)
        self.image = self.make_image(self.masked_matrix, self.color)

    def data_analiyze(self, data):
        # 0b0001: neric mode
        # 0b0010: alphaneric mode
        # 0b0100: 8-bit byte mode
        # 0b1000: kanji mode
        return 0b0100

    def data_encode(self, data):
        encoded_data = data.encode("utf-8")
        mode_instruction = Bitarray([self.mode], 4)

        data_length = len(encoded_data)
        instruction_bit_length = self.get_instruction_bit_length(self.version, self.mode)
        data_length_instruction = Bitarray([data_length], instruction_bit_length)

        encoded_data_bitarray = Bitarray(encoded_data)

        return mode_instruction + data_length_instruction + encoded_data_bitarray

    def get_instruction_bit_length(self, version, mode):
        length_table = [[10,9,8,8], #1-9
                        [12,11,16,10], #10-26
                        [14,13,16,12], #27-40
                        ]
        def mode_to_index(mode):
            for i in range(4):
                if (mode >> i) & 1:
                    return i

        index = mode_to_index(mode)
        if version < 10:
            return length_table[0][index]
        elif version < 27:
            return length_table[1][index]
        else:
            return length_table[2][index]

    def weed_padding(self, data_code, data_code_length):
        WEEDS = [0b11101100, 0b00010001]
        if len(data_code) >= data_code_length:
            return data_code
        pad = data_code_length - len(data_code)
        for i in range(pad):
            data_code.append(WEEDS[i%2])
        return data_code

    def make_matrix(self, code_bit_array):
        matrix = self.init_matrix()
        matrix = self.set_position_pattern(matrix)
        matrix = self.set_position_pattern2(matrix)
        matrix = self.set_timing_pattern(matrix)
        matrix = self.set_dark_module(matrix)
        matrix = self.set_format_information(matrix)

        if self.version >= 7:
            matrix = self.set_version_information(matrix)

        self.flag_matrix = [[value for value in row] for row in matrix]
        matrix = self.put(matrix, code_bit_array)
        matrix = self.fill_rest(matrix)

        return matrix

    def init_matrix(self):
        self.w = self.h = w = h = 17 + self.version * 4
        matrix = [[None for col in range(w)] for row in range(h)]
        return matrix

    def set_position_pattern(self, matrix):
        BASE = [[1,1,1,1,1,1,1,0],
                [1,0,0,0,0,0,1,0],
                [1,0,1,1,1,0,1,0],
                [1,0,1,1,1,0,1,0],
                [1,0,1,1,1,0,1,0],
                [1,0,0,0,0,0,1,0],
                [1,1,1,1,1,1,1,0],
                [0,0,0,0,0,0,0,0],
        ]
        for y in range(len(BASE)):
            for x in range(len(BASE[y])):
                matrix[y][x] = BASE[y][x]
                matrix[y][-1-x] = BASE[y][x]
                matrix[-1-y][x] = BASE[y][x]
        return matrix

    def set_timing_pattern(self, matrix):
        for x in range(8, self.w-7):
            matrix[6][x] = (x+1) % 2
            matrix[x][6] = (x+1) % 2
        return matrix

    def set_position_pattern2(self, matrix):
        # position pattern
        PATTERN_POSITION = PATTERN_POSITION_TABLE[self.version - 1]
        for x in PATTERN_POSITION:
            for y in PATTERN_POSITION:
                if matrix[y][x] != None: continue
                for i in range(-2, 3):
                    for j in range(-2, 3):
                        matrix[y+i][x+j] = 1 if abs(i) == 2 or abs(j) == 2 or (i == j == 0) else 0

        return matrix

    def set_dark_module(self, matrix):
        matrix[-8][8] = 1
        return matrix

    def set_format_information(self, matrix):
        # format information
        format_info = []
        if self.error_correct_level == self.ERROR_CORRECT_L:
            format_info.extend([0,1])
        elif self.error_correct_level == self.ERROR_CORRECT_M:
            format_info.extend([0,0])
        elif self.error_correct_level == self.ERROR_CORRECT_Q:
            format_info.extend([1,1])
        elif self.error_correct_level == self.ERROR_CORRECT_H:
            format_info.extend([1,0])

        for i in range(3):
            format_info.append((self.mask_pattern>>(2-i)) & 1)
        
        bch_code = gf_poly_div(format_info+[0]*(15-5), G15)[-1]
        format_info += bch_code
        mask = [1,0,1,0,1,0,0,0,0,0,1,0,0,1,0]
        format_info = [i^j for i, j in zip(format_info, mask)][::-1]

        for i, f in enumerate(format_info):
            if i < 8:
                matrix[8][-1-i] = f
                if matrix[i][8] == None:
                    matrix[i][8] = f
                else:
                    matrix[i+1][8] = f
            else:
                matrix[-7+i-8][8] = f
                if matrix[8][7-i+8] == None:
                    matrix[8][7-i+8] = f
                else:
                    matrix[8][7-i-1+8] = f
        
        return matrix
    
    def set_version_information(self, matrix):
        # format information
        version_info = [1 if bit else 0 for bit in Bitarray([self.version], 6).array]
        
        bch_code = gf_poly_div(version_info+[0]*12, G18)[-1]
        version_info += bch_code

        for i in range(6):
            for j in range(3):
                matrix[5-i][-9-j] = version_info[i * 3 + j]
                matrix[-9-j][5-i] = version_info[i * 3 + j]

        return matrix

    def put(self, matrix, code_bit_array):
        x = y = self.w - 1
        mx, my, sign = -1, 0, -1
        for bit in code_bit_array:
            while matrix[y][x] != None:
                if y + sign * my < 0 or y + sign * my >= self.h:
                    sign *= -1
                    mx = 1
                    my = 1
                    x -= 2
                    y -= sign * my
                x += mx
                y += sign * my
                if x == 6:
                    x -= 1

                mx *= -1
                my = (my + 1) % 2
            matrix[y][x] = 1 if bit else 0
        return matrix
            
    def fill_rest(self, matrix):
        for y in range(self.h):
            for x in range(self.w):
                if matrix[y][x] == None:
                    matrix[y][x] = 0
        return matrix

    def mask(self, mask_pattern):
        masked_matrix = self.matrix
        functions = [
        (lambda i ,j: 1 if (i+j) % 2 == 0 else 0),
        (lambda i ,j: 1 if i % 2 == 0 else 0),
        (lambda i ,j: 1 if j % 3 == 0 else 0),
        (lambda i ,j: 1 if (i+j) % 3 == 0 else 0),
        (lambda i ,j: 1 if (i // 2 + j // 3) % 2 else 0),
        (lambda i ,j: 1 if (i*j) % 2 + (i*j) % 3 == 0 else 0),
        (lambda i ,j: 1 if ((i*j) % 2 + (i*j) % 3) % 2 == 0 else 0),
        (lambda i ,j: 1 if ((i+j) % 2 + (i*j) % 3) % 2 == 0 else 0),
        ]
        func = functions[mask_pattern]
        for y, row in enumerate(self.flag_matrix):
            for x, value in enumerate(row):
                if value == None:
                    masked_matrix[y][x] ^= func(y, x)
        return masked_matrix

    def make_image(self, matrix, color):
        color_tuple = ImageColor.getrgb(color)
        color_tuple = tuple(255 - c for c in color_tuple)
        mid_image = Image.fromarray(numpy.uint8(matrix))
        mid_image = mid_image.convert('RGB')
        rgb_matrix = numpy.asarray(mid_image, dtype=numpy.uint8)
        colored_matrix = numpy.asarray(255 - rgb_matrix * color_tuple, dtype=numpy.uint8)
        img = Image.fromarray(colored_matrix)
        return img

    def set_blocks(self, blocks):
        self.data_blocks = blocks
        self.processed_data_code = Block.integrate([block.code for block in self.data_blocks]).code
        self.processed_error_code = Block.integrate(self.error_blocks).code
        self.processed_code = self.processed_data_code + self.processed_error_code

        self.matrix = self.make_matrix(Bitarray(self.processed_code).array)

        self.masked_matrix = self.mask(self.mask_pattern)
        self.image = self.make_image(self.masked_matrix, self.color)

    def print_matrix(self, matrix):
        for row in matrix:
            for col in row:
                print(col, end="") if col != None else print(2, end="")
            print()
    

def main():
    import sys
    data, version = sys.argv[1], int(sys.argv[2])

    qr = QR(data, version, 3, color="#000000")
    qr.image.show()

if __name__ == '__main__':
    data = "test string"
    version = 3

    import sys
    data, version = sys.argv[1], int(sys.argv[2])

    import qrcode
    q = qrcode.QRCode(version=version, error_correction=qrcode.constants.ERROR_CORRECT_H)
    q.add_data(data)
    q.make()

    qr = QR(data, version, 3)