from core.base.BaseParser import BaseParser
from core.format.Format import Format


class MotorolaMSB(BaseParser):
    """Motorola MSB 格式：起始位为 MSB，先转换为 LSB 再使用大端规则"""

    def define_format(self) -> Format:
        return Format.MOTOROLA_MSB

    def get_bit_positions(self, start_bit: int, bit_length: int):
        lsb = self.__msb_to_lsb(start_bit, bit_length)
        # 复用 Motorola LSB 的位置生成
        return BaseParser.get_parser(Format.MOTOROLA_LSB).get_bit_positions(lsb, bit_length)

    @classmethod
    def __msb_to_lsb(cls, msb_start_bit: int, length: int) -> int:
        byte = msb_start_bit // 8
        bit = msb_start_bit % 8
        for _ in range(length - 1):
            if bit == 0:
                byte += 1
                bit = 7
            else:
                bit -= 1
        return byte * 8 + bit
