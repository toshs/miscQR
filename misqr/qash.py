from .util.filter import BayerFilter
from .util.constants import W, K
from .util.rs import rs
from .util.block import Block
from .util.qr import QR
import qrcode
import numpy as np
import sys
import random
import itertools

class Qash:
    """
    QR against shoulder hacking(Qash)に関する属性値やヘルパー関数を保持する。

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
    qash:
        ランダム化されたQRコード
    """
    
    def __init__(self, 
                 data,
                 version,
                 error_correction=qrcode.constants.ERROR_CORRECT_H,
                 pixel_size=1,
                 box_size=20,
                 border=4,
                 color="#888888",
                 insertion=1):

        self.data = data
        self.version = version
        self.pixel_size = pixel_size
        self.box_size = box_size
        self.border = border
        self.color = color
        self.insertion = insertion

        self.qr = QR(data, version, error_correction, color=color)

        self.version = self.qr.version
        self.error_correction = self.qr.error_correct_level

        self.code = self.qr.processed_code #[codewords]
        self.matrix = self.qr.matrix
        self.possible_error = self.calc_error_symbol()  # ブロックごとのエラー許容数

        # QRを限界まで壊す 
        blocks = self.qr.data_blocks
        for i in range(len(blocks)):
            blocks[i].randomize(self.possible_error[i]-self.insertion+1)
        self.qr.set_blocks(blocks)
        
        self.qr.image = self.qr.image.resize((self.qr.image.width * self.box_size, self.qr.image.height * self.box_size))

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

    @classmethod
    def make_qr(cls, data, version, error_correction):
        qr = qrcode.QRCode(version=version, 
            error_correction=error_correction, 
        )
        qr.add_data(data)
        qr.make()
        return qr


def main():
    # Get Time
    from time import gmtime, strftime
    T = strftime('%Y%m%d%H%M%S', gmtime())

    if len(sys.argv) < 2:
        print("usage: python3 qash.py <data>")
        sys.exit()
    data = sys.argv[1]

    filename = data + T

    # Generate Qash
    qash = Qash(data=data, version=4 ,error_correction=3)

    # Generate False Pattern
    # S = np.array([255,255,255])//4*3
    f = BayerFilter(qash.box_size//2, qash.box_size//2)
    f.pix = np.array(
        [[W, K],
        [K, K]]
    )
    f.makeBayerFilter()
    f.makeImage()
    pixel = f.image

    # Set Pattern to Image
    white_pixel_position = np.where(np.logical_not(np.array(qash.qr.masked_matrix)))
    tx, ty = 0, 0
    for y, x in zip(white_pixel_position[0], white_pixel_position[1]):
        if x > 9 and y > 9:
            tx, ty = x, y
            break

    qash.set_pixel(pixel, tx, ty)
    qash.qr.image.show()

if __name__ == "__main__":
    main()