from core.base.BaseParser import BaseParser
from core.base.Format import Format


class MessageParser:
    """报文解析统一入口"""

    @staticmethod
    def init_parser():
        BaseParser.auto_register_formats()

    @staticmethod
    def parse_signal(data_bytes: list, fmt: Format, start_bit: int, bit_length: int, factor: float = 1.0,
                     offset: float = 0.0) -> dict:
        """
        解析 CAN 报文信号，返回包含原始值和物理值的字典。
        :param data_bytes: 字节列表，索引0对应 byte0
        :param fmt: 格式，可选 'intel', 'motorola_lsb', 'motorola_msb'
        :param start_bit: 起始位
        :param bit_length: 信号长度 (bits)
        :param factor: 精度
        :param offset: 偏移量
        :return: {'raw': int, 'physical': float}
        """
        parser = BaseParser.get_parser(fmt)
        if parser is None:
            raise ValueError(f"不支持的格式: '{fmt}'，可选 'intel', 'motorola_lsb', 'motorola_msb'")

        raw = parser.parse_raw(data_bytes, start_bit, bit_length)
        physical = raw * factor + offset
        return {'raw': raw, 'physical': physical}
