from dataclasses import dataclass


@dataclass
class SignalData:
    can_id: int  # 报文 ID（整数）
    signal_name: str  # 信号名称
    start_bit: int  # 起始位
    bit_length: int  # 位长度
    factor: float  # 系数
    offset: float  # 偏移量
