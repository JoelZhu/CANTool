from core.base.BaseParser import BaseParser
from core.format.Format import Format


class MotorolaLSBParser(BaseParser):
    """Motorola LSB 格式：起始位为 LSB，大端字节序填充（向低地址回卷）"""

    def define_format(self) -> Format:
        return Format.MOTOROLA_LSB

    def get_bit_positions(self, start_bit, bit_length):
        positions = []
        byte = start_bit // 8
        bit = start_bit % 8
        for _ in range(bit_length):
            positions.append(byte * 8 + bit)
            bit += 1
            if bit > 7:
                bit = 0
                byte -= 1
        return positions
