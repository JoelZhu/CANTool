from core.base.BaseParser import BaseParser
from core.format.Format import Format


class Intel(BaseParser):
    """Intel 格式（小端）：起始位为 LSB，位号连续递增"""

    def define_format(self) -> Format:
        return Format.INTEL

    def get_bit_positions(self, start_bit: int, bit_length: int):
        return [start_bit + i for i in range(bit_length)]
