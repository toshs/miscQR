from .rs import rs
import reedsolo
import random
import itertools

class Block():

    def __init__(self, code):
        self.code = code

    def randomize(self, n):
        """
        data codeのうち、先頭のn moduleをrandomizeする。

        Parameters
        --------
        n : int

        Notes
        --------
        randomizeされたコードをsetします。
        
        """
        randomized_code = self.code[:]
        for i in range(n):
            while True:
                r = random.randint(0, 1<<8)
                if randomized_code[i] != r:
                    randomized_code[i] = r
                    break
        
        self.code = randomized_code
        
    def calculate_error_correction_code(self, error_code_length):
        rsc = reedsolo.RSCodec(error_code_length)
        error_block = [i for i in rsc.encode(self.code)[-error_code_length:]]
        return error_block

    @classmethod
    def integrate(cls, blocks=[]):
        code = []
        for data in itertools.zip_longest(*blocks):
            for d in data:
                if d == None:
                    continue
                code.append(d)
                
        return Block(code) 

    @classmethod
    def divide_into_data_block(cls, code, version, error_correction):
        block_length, code_length, data_code_length, blocks_info = cls.get_block_info(version, error_correction)
        blocks = [[] for _ in range(block_length)]
        block_data_length = [range(block_info[2]) for block_info in blocks_info]
        index = 0
        for row in itertools.zip_longest(*block_data_length):
            for i, item in enumerate(row):
                if item == None:
                    continue
                blocks[i].append(code[index])
                index += 1
        
        return blocks

    @classmethod
    def divide_into_block(cls, code, version, error_correct_level):
        block_length, code_length, data_code_length, blocks_info = cls.get_block_info(version, error_correct_level)
        blocks = [[] for _ in range(block_length)]
        block_data_length = [block_info[2] for block_info in blocks_info]

        base = 0
        for i, l in enumerate(block_data_length):
            blocks[i] = Block(code[base:base+l])
            base += l

        return blocks

    @classmethod
    def get_block_info(cls, version, error_correct_level):
        block_info = rs[(version-1) * 4 + error_correct_level]
        block_length = 0
        code_length = 0
        data_code_length = 0

        blocks_info = []

        for i in range(len(block_info) // 3):
            sub_block_info = block_info[i*3: i*3+3]
            block_length += sub_block_info[0]
            code_length += sub_block_info[1] * sub_block_info[0]
            data_code_length += sub_block_info[2] * sub_block_info[0]
            for _ in range(sub_block_info[0]):
                blocks_info.append(sub_block_info)

        return block_length, code_length, data_code_length, blocks_info
