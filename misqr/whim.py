from .util.filter import BayerFilter
from .util.constants import W, K
from .util.rs import rs
from .util.block import Block
from .util.qr import QR
from .util.bitarray import Bitarray
from PIL import Image
import qrcode
import numpy as np
import sys
import random
import itertools

class Whim:
    """
    Whimsical QRの再現。関連する属性値やヘルパー関数を保持する。

    Attributes
    --------
    data: string
        QRコードのデータ(ex. "http://example.com", "Secret ID", etc...)
    pixel_size: int
        False Patternの最小単位[px]
    box_size: int
        QRコードのモジュールの一辺のサイズ
        QRコードの一辺はpixel_size * box_size[px]になる
    border: int
        QRコードの余白
    qr: Object
        データから生成した通常のQRコード
    version: int
        QRコードのバージョン情報
    error_correction: int
        QRコードの誤り訂正レベル。(L, M, H, Q) = (0, 1, 2, 3)
    block_num: int
        QRコードのブロック数
    code_length: int
        QRコードの語数
    data_code_length: int
        QRコードのデータ語の語数
    error_code_length: int
        QRコードの誤り訂正語の語数
    code: list
        QRコードの内部のコード語(ex.[64, 1, 4, 123, ... , 193])
    blocks: list
        QRコードのブロックごとのコード語
    whim:
        ランダム化されたQRコード
    """
    
    def __init__(self, 
                 data,
                 version,
                 error_correction=qrcode.constants.ERROR_CORRECT_H,
                 pixel_size=1,
                 box_size=20,
                 border=4,
                 insertion=1):

        self.data = data
        self.version = version
        self.pixel_size = pixel_size
        self.box_size = box_size
        self.border = border
        self.insertion = insertion

        self.qr = QR(data, version, error_correction)

        self.version = self.qr.version
        self.error_correction = self.qr.error_correct_level

        self.code = self.qr.data_code  # [codewords]
        self.possible_error = self.calc_error_symbol()
        
        # blocks = self.qr.data_blocks
        # blocks[0].randomize(self.possible_error[0]-self.insertion+1)
        # self.qr.set_blocks(blocks)

    # QR画像の(x, y)にpixel(matrix)を貼り付ける
    def set_pixel(self, pixel, x, y):
        #offset = self.qr.box_size * self.qr.border
        offset = 0
        x = x * self.box_size
        y = y * self.box_size
        self.qr.image.paste(pixel, (offset+x,offset+y))

    # ブロックごとに許容する最大エラー数を返す
    def calc_error_symbol(self):
        blocks = rs[(self.version-1) * 4 + self.error_correction]
        possible_errors = []
        for i in range(len(blocks)//3):
            block = blocks[i*3:i*3+3]
            error_code_length = block[1] - block[2]
            for _ in range(block[0]):
                possible_errors.append(error_code_length // 2)
        return possible_errors

    # data配列[a,b,c,...]からQRを生成
    def make_qr_from_data(self, data):
        qr = self.make_qr(self.data, self.version, self.qr.error_correct_level)
        qr.mask_pattern = qr.best_mask_pattern()
        qr.data_cache = data
        for r, row in enumerate(qr.modules):
            for c, col in enumerate(row):
                qr.modules[r][c] = None
        qr.makeImpl(False, qr.mask_pattern)
        return qr

    def search_similar_qr(self, index=0):
        ret = {}
        character = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
        for c in character:
            if self.data[index] == c: continue
            candidate = self.data[:index] + c + (self.data[index+1:] if index != -1 else "")
            cand_qr = QR(candidate, self.version, self.error_correction)
            if self.diff(self.qr.processed_code, cand_qr.processed_code) == self.possible_error[0] * 2 + 1:
                left, right, found = self.mix(self.qr.processed_code, cand_qr.processed_code, self.possible_error[0])
                if found == -1: continue
                cand_qr.processed_code = left
                cand_qr.matrix = cand_qr.make_matrix(Bitarray(cand_qr.processed_code).array)
                cand_qr.masked_matrix = cand_qr.mask(cand_qr.mask_pattern)
                cand_qr.image = cand_qr.make_image(cand_qr.masked_matrix, cand_qr.color)
                src = np.asarray(cand_qr.image, dtype=np.uint16)

                cand_qr.processed_code = right 
                cand_qr.matrix = cand_qr.make_matrix(Bitarray(cand_qr.processed_code).array)
                cand_qr.masked_matrix = cand_qr.mask(cand_qr.mask_pattern)
                cand_qr.image = cand_qr.make_image(cand_qr.masked_matrix, cand_qr.color)
                dst = np.asarray(cand_qr.image, dtype=np.uint16)

                mixed = np.asarray((src + dst)//2, dtype=np.uint8)
                middle = Image.fromarray(mixed)

                ret[candidate] = middle
        return ret


        part = self.data.split(".")
        for i in range(len(part[0])):
            for c in character:
                if part[0][i] == c: continue
                candidate = part[0][:i] + c + part[0][i+1:]
                candidate = ".".join([candidate] + part[1:])
                cand_qr = QR(candidate, self.version, self.error_correction)
                if self.diff(self.qr.processed_code, cand_qr.processed_code) == self.possible_error[0] * 2 + 1:
                    left, right, index = self.mix(self.qr.processed_code, cand_qr.processed_code, self.possible_error[0])
                    if index == -1: continue
                    cand_qr.processed_code = left
                    cand_qr.matrix = cand_qr.make_matrix(Bitarray(cand_qr.processed_code).array)
                    cand_qr.masked_matrix = cand_qr.mask(cand_qr.mask_pattern)
                    cand_qr.image = cand_qr.make_image(cand_qr.masked_matrix, cand_qr.color)
                    src = np.asarray(cand_qr.image, dtype=np.uint16)

                    cand_qr.processed_code = right 
                    cand_qr.matrix = cand_qr.make_matrix(Bitarray(cand_qr.processed_code).array)
                    cand_qr.masked_matrix = cand_qr.mask(cand_qr.mask_pattern)
                    cand_qr.image = cand_qr.make_image(cand_qr.masked_matrix, cand_qr.color)
                    dst = np.asarray(cand_qr.image, dtype=np.uint16)

                    mixed = np.asarray((src + dst)//2, dtype=np.uint8)
                    middle = Image.fromarray(mixed)

                    ret[candidate] = middle
        return ret

    @classmethod
    def make_qr(cls, data, version, error_correction):
        qr = qrcode.QRCode(version=version, 
            error_correction=error_correction, 
        )
        qr.add_data(data)
        qr.make()
        return qr

    @classmethod
    def diff(cls, code1, code2):
        count = 0
        for c1, c2 in zip(code1, code2):
            if c1 != c2:
                count += 1
        return count

    @classmethod
    def mix(cls, code1, code2, possible_error):
        count = 0
        index = -1
        left = []
        right = []
        for i, (c1, c2) in enumerate(zip(code1, code2)):
            if c1 != c2:
                if index == -1 and bin(c1 ^ c2).count('1') == 1:
                    index = i
                    left.append(c1)
                    right.append(c2)
                    continue
                if count < possible_error:
                    left.append(c1)
                    right.append(c1)
                else:
                    left.append(c2)
                    right.append(c2)
                count += 1
            else:
                left.append(c1)
                right.append(c1)
        return left, right, index 
                
def main():
    data = sys.argv[1]
    index = int(sys.argv[2])

    # Generate Whim
    whim = Whim(data=data, version=4 ,error_correction=3)
    ret = whim.search_similar_qr(index)
    print('Option')
    for i, (key, value) in enumerate(ret.items()):
        print('', key)
    option = input('Select:')
    ret[option].show()


if __name__ == "__main__":
    main()