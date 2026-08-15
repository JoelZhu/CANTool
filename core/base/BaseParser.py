import importlib
import pkgutil
from abc import ABC, abstractmethod
from typing import Type, Dict

from core.base.Format import Format

FORMAT_PKG_NAME = "core.format"


class BaseParser(ABC):
    """CAN 信号解析器抽象基类"""

    # 注册表：Format -> Parser类
    _parser_dict: Dict[Format, 'BaseParser'] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # 要求子类必须实现 define_format，用其返回值作为注册键
        # 这里通过实例化一个临时对象来获取 Format（如果你不希望实例化，可改为类属性）
        # 推荐改为类属性：在子类中直接定义 format = Format.INTEL
        instance: cls
        try:
            # 方式1：调用无参构造获取 Format（要求子类构造器无参）
            instance = cls()
            fmt = instance.define_format()
        except Exception:
            # 方式2：使用类变量，更安全
            raise TypeError(f"Create instance of {cls.__name__} or get it's format failed.")

        if instance is None:
            raise ValueError(f"Create instance of {cls.__name__} failed.")
        if fmt in cls._parser_dict:
            raise ValueError(f"Format {fmt} already registered by {cls._parser_dict[fmt].__name__}.")

        cls._parser_dict[fmt] = instance

    @abstractmethod
    def define_format(self) -> Format:
        pass

    @abstractmethod
    def get_bit_positions(self, start_bit: int, bit_length: int) -> list:
        """返回从 LSB 到 MSB 的位索引列表"""
        pass

    def parse_raw(self, data_bytes: list, start_bit: int, bit_length: int) -> int:
        """从报文中提取原始整数值"""
        positions = self.get_bit_positions(start_bit, bit_length)
        total_bits = len(data_bytes) * 8
        value = 0
        for i, pos in enumerate(positions):
            if pos < 0 or pos >= total_bits:
                raise ValueError(f"Bit position: {pos} out of range (0-{total_bits - 1})")
            byte_idx = pos // 8
            bit_idx = pos % 8
            if data_bytes[byte_idx] & (1 << bit_idx):
                value |= (1 << i)
        return value

    @classmethod
    def auto_register_formats(cls):
        """
        自动加载指定包下的所有模块，触发子类注册
        """
        package = importlib.import_module(FORMAT_PKG_NAME)
        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            # 动态导入模块，触发 __init_subclass__ 执行
            importlib.import_module(f"{FORMAT_PKG_NAME}.{module_name}")

    @classmethod
    def get_parser(cls, formatter: Format) -> 'BaseParser':
        parser = cls._parser_dict.get(formatter)
        if parser is None:
            raise ValueError(f"Unregistered format: {formatter}.")
        return parser

    @classmethod
    def get_all_parsers(cls) -> Dict[Format, 'BaseParser']:
        return cls._parser_dict
