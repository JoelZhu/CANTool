from core.base.BaseParser import BaseParser


class MessageParser:
    """报文解析统一入口"""

    @staticmethod
    def init_parser():
        BaseParser.auto_register_formats()

    @staticmethod
    def parse_signal(parser: BaseParser, data_bytes: list, start_bit: int, bit_length: int, factor: float = 1.0,
                     offset: float = 0.0) -> dict:
        """
        解析 CAN 报文信号，返回包含原始值和物理值的字典。
        :param parser: 报文解析类，可选格式参考 `Format` 的定义
        :param data_bytes: 字节列表，索引0对应 byte0
        :param start_bit: 起始位
        :param bit_length: 信号长度 (bits)
        :param factor: 精度
        :param offset: 偏移量
        :return: {'raw': int, 'physical': float}
        """
        if parser is None:
            raise ValueError("Parser cannot be None.")

        raw = parser.parse_raw(data_bytes, start_bit, bit_length)
        physical = raw * factor + offset
        return {'raw': raw, 'physical': physical}

    @staticmethod
    def generate_signal(parser: BaseParser, byte_length: int, start_bit: int, bit_length: int, values: dict) -> list:
        """
        根据物理值生成对应的 CAN 数据字节。
        :param parser: 具体的解析器实例（如 IntelParser）
        :param byte_length: 生成的消息总字节数
        :param start_bit: 起始位
        :param bit_length: 信号长度
        :param values: {'raw': int} 或者 {'physical': float, 'factor': float, 'offset': float} 二选一
        :return: 字节列表
        """
        if parser is None:
            raise ValueError("Parser cannot be None.")

        raw_value: int = values.get('raw')
        if raw_value is None:
            physical = values.get('physical')
            factor = values.get('factor')
            offset = values.get('offset')
            if physical is None or factor is None or offset is None:
                raise ValueError("Raw or Physical can't be all none.")
            raw_value = int((physical - offset) / factor)
            if raw_value is None:
                raise ValueError(f"Physical value is illegal, {physical}.")

        return parser.generate_message(raw_value, byte_length, start_bit, bit_length)

    @staticmethod
    def get_all_positions(parser: BaseParser, byte_length: int, start_bit: int, bit_length: int) -> list:
        """
        获取全部的数据位。
        :param parser: 具体的解析器实例（如 IntelParser）
        :param byte_length: 字节数
        :param start_bit: 起始位
        :param bit_length: 信号长度
        :return: 字节列表
        """
        if parser is None:
            raise ValueError("Parser cannot be None.")

        return parser.get_all_valid_bit_positions(byte_length, start_bit, bit_length)
