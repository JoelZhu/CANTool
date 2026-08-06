from core.base.BaseParser import BaseParser
from core.base.Format import Format
from core.format.MotorolaLSB import MotorolaLSBParser


class MotorolaMSBParser(BaseParser):
    """Motorola MSB 格式：起始位为 MSB，先转换为 LSB 再使用大端规则"""

    def define_format(self) -> Format:
        return Format.MOTOROLA_MSB

    @staticmethod
    def msb_to_lsb(msb, length):
        byte = msb // 8
        bit = msb % 8
        for _ in range(length - 1):
            if bit == 0:
                byte += 1
                bit = 7
            else:
                bit -= 1
        return byte * 8 + bit

    def get_bit_positions(self, start_bit, bit_length):
        lsb = self.msb_to_lsb(start_bit, bit_length)
        # 复用 Motorola LSB 的位置生成
        return MotorolaLSBParser().get_bit_positions(lsb, bit_length)
