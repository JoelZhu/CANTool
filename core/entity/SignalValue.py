from dataclasses import dataclass


@dataclass
class SignalValue:
    raw_value: int  # 总线值
    physical_value: float  # 物理值
