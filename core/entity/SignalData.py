from dataclasses import dataclass

from core.format.Format import Format


@dataclass
class SignalData:
    format: Format  # 报文格式
    can_id: int  # 报文 ID（整数）
    direction: str  # 方向
    signal_name: str  # 信号名称
    start_bit: int  # 起始位
    bit_length: int  # 位长度
    factor: float  # 系数
    offset: float  # 偏移量
