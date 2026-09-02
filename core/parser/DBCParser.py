import os
import re
from re import Match
from typing import List, Optional, Tuple, Dict, Callable

from core.Util import print_debug, print_error, settings
from core.base.BaseParser import BaseParser
from core.entity.SignalData import SignalData
from core.format.Format import Format

SIGNAL_PATTERN = re.compile(r'(\d+)\|(\d+)@([01])([+-])\s*\(\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)\s*,\s*([-+]?'
                            r'(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)\s*\)')

SIGNAL_BO_PATTERN = re.compile(r'^BO_\s+(\d+)\s+([^:]+):\s*\d+\s+(\S+)')

BYTE_ORDER_MOTOROLA = 0

# DBC 持久化路径
KEY_DBC_PATHS = "DBCPaths"
DBC_PATH_SPLITER = ","

# 储存是否 LSB 优先
KEY_LSB_FIRST = "LSBFirst"
VALUE_LSB_FIRST = 1
VALUE_NO_LSB_FIRST = 0


class DBCParser:
    loaded_dbc: Dict[str, List[SignalData]] = dict()
    is_lsb_first_in_motorola: bool = True

    dbc_change_callback: Callable[[], None] = None

    @classmethod
    def init_parser(cls):
        try:
            cls.is_lsb_first_in_motorola = int(settings.value(KEY_LSB_FIRST, VALUE_LSB_FIRST)) == VALUE_LSB_FIRST
        except Exception as e:
            cls.is_lsb_first_in_motorola = True
            print_error(f"Got LSB first failed, {str(e)}")

        cls.__load_all_dbc__()

    @classmethod
    def register_dbc_change_callback(cls, callback: Callable[[], None]):
        if callback:
            cls.dbc_change_callback = callback

    @classmethod
    def switch_lsb_first(cls, is_lsb_first: bool):
        if is_lsb_first == cls.is_lsb_first_in_motorola:
            return
        settings.setValue(KEY_LSB_FIRST, VALUE_LSB_FIRST if is_lsb_first else VALUE_NO_LSB_FIRST)
        cls.is_lsb_first_in_motorola = is_lsb_first
        # 重新加载全部 DBC
        cls.__load_all_dbc__(True)

    @classmethod
    def get_is_lsb_first(cls) -> bool:
        return cls.is_lsb_first_in_motorola

    @classmethod
    def load_dbc(cls, file_path: str) -> bool:
        """
        解析 DBC 文件，提取所有报文中的信号信息。
        :param file_path: DBC 文件路径
        :return 加载结果
        """
        signals: List[SignalData] = []
        current_can_id: Optional[int] = None
        print_debug(f"To load DBC file: {file_path}.")

        if not os.path.exists(file_path):
            print_error(f"File: {file_path} not exists.")
            return False

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file_reader:
            for raw_line in file_reader:
                line = cls.__clean_line__(raw_line)
                if not line:
                    continue

                # 尝试更新当前报文信息（CAN ID 和发送节点）
                bo_info = cls.__parse_bo_line__(line)
                if bo_info is not None:
                    current_can_id, _ = bo_info
                    continue  # BO_ 行本身不包含信号，直接处理下一行

                # 尝试解析信号
                signal = cls.__parse_signal__(line, current_can_id)
                if signal is not None:
                    signals.append(signal)

        load_result = False
        if signals.__len__() > 0:
            print_debug(f"DBC file: {file_path} loaded successfully.")
            cls.loaded_dbc[file_path] = signals
            path_list = cls.query_stored_dbc_files()
            if file_path not in path_list:
                if path_list.__len__() == 0:
                    path_list = [file_path]
                else:
                    path_list.append(file_path)
                new_dbc_paths = DBC_PATH_SPLITER.join(path_list)
                settings.setValue(KEY_DBC_PATHS, new_dbc_paths)
                load_result = True
                # 通知监听者 DBC 发生了变化
                if cls.dbc_change_callback:
                    cls.dbc_change_callback()
        else:
            print_error(f"DBC file: {file_path} loaded failed.")
        return load_result

    @classmethod
    def unload_dbc(cls, file_path: str):
        try:
            del cls.loaded_dbc[file_path]
        except Exception as e:
            print_error(f"DBC file: {file_path} not exists, unload failed: {str(e)}.")

        path_list = cls.query_stored_dbc_files()
        if file_path in path_list:
            path_list.remove(file_path)
            new_dbc_paths = DBC_PATH_SPLITER.join(path_list)
            settings.setValue(KEY_DBC_PATHS, new_dbc_paths)
            # 通知监听者 DBC 发生了变化
            if cls.dbc_change_callback:
                cls.dbc_change_callback()

    @classmethod
    def query_stored_dbc_files(cls) -> list:
        """
        查找当前已经存储的 DBC 文件列表
        :return: 文件列表
        """
        stored_dbc_paths = settings.value(KEY_DBC_PATHS, "")
        if stored_dbc_paths == "":
            return list()
        path_list = stored_dbc_paths.split(DBC_PATH_SPLITER)
        return path_list

    @classmethod
    def query_all_loaded_signals(cls) -> List[SignalData]:
        all_signals = []
        for signal_list in cls.loaded_dbc.values():
            all_signals.extend(signal_list)
        return all_signals

    @classmethod
    def find_signal_from_loaded_dbc(cls, searching_signal_name: str) -> List[SignalData]:
        """
        查找已经加载的 DBC 文件中，对应的信号
        :param searching_signal_name: 检索的信号名
        :return: 查找到的信号，无则返回 None（最多返回 5 个）
        """
        results = []
        search_lower = searching_signal_name.lower()

        # 遍历所有已加载文件中的信号
        for signals in cls.loaded_dbc.values():
            for signal in signals:
                if search_lower in signal.signal_name.lower():
                    results.append(signal)
                    if len(results) >= 5:
                        return results[:5]
        return results[:5]

    @classmethod
    def __load_all_dbc__(cls, reset: bool = False):
        stored_dbc_files = cls.query_stored_dbc_files()
        if reset:
            for dbc_file in stored_dbc_files:
                cls.unload_dbc(dbc_file)
        print_debug(f"To load all loaded DBC files: {stored_dbc_files}.")
        for dbc_file in stored_dbc_files:
            cls.load_dbc(dbc_file)

    @classmethod
    def __clean_line__(cls, line: str) -> str:
        # 去除行内注释和首尾空白，返回处理后的字符串（可能为空）
        if '//' in line:
            line = line.split('//', 1)[0]
        return line.strip()

    @classmethod
    def __parse_bo_line__(cls, line: str) -> Optional[Tuple[int, str]]:
        if not line.startswith('BO_'):
            return None
        # 使用正则提取：BO_ <id> <name>: <size> <transmitter>
        match = re.match(SIGNAL_BO_PATTERN, line)
        if match:
            can_id = int(match.group(1), 0)
            transmitter = match.group(3)
            return can_id, transmitter
        return None

    @classmethod
    def __parse_can_id__(cls, line: str) -> Optional[int]:
        # 如果该行是 BO_ 定义行，解析并返回 CAN ID（支持十进制或十六进制）。否则返回 None。
        if not line.startswith('BO_'):
            return None
        parts = line.split()
        if len(parts) >= 2:
            try:
                return int(parts[1], 0)  # int(..., 0) 自动识别十进制和十六进制
            except ValueError:
                return None
        return None

    @classmethod
    def __parse_signal__(cls, line: str, can_id: Optional[int]) -> Optional[SignalData]:
        # 如果该行是 SG_ 定义行且当前 CAN ID 有效，尝试解析信号信息。成功返回 SignalData，否则返回 None。
        if not line.startswith('SG_') or can_id is None:
            return None

        # 用冒号分割信号名部分和属性部分
        if ':' not in line:
            return None
        left, right = line.split(':', 1)
        left = left.strip()
        left_parts = left.split()
        if len(left_parts) < 2:
            return None
        signal_name = left_parts[1]

        match = SIGNAL_PATTERN.search(right)
        if match:
            return cls.__parse_signal_actual__(can_id, signal_name, match)

        print_debug(f"Signal parse failed, content: {line}")
        return None

    @classmethod
    def __parse_signal_actual__(cls, can_id: Optional[int], signal_name: str, match: Optional[Match]) -> SignalData:
        byte_order = int(match.group(3))
        start_bit_raw = int(match.group(1))
        bit_length = int(match.group(2))
        if byte_order == BYTE_ORDER_MOTOROLA:  # Motorola
            if cls.is_lsb_first_in_motorola:
                signal_format = Format.MOTOROLA_LSB
                # 转换成 LSB 的起始位，按照 LSB 方式标记（由于 LSB 和 MSB 的排序方式一样，只是起始位不一样，取字节位列表的第一个即可）
                bit_positions = BaseParser.get_parser(Format.MOTOROLA_MSB).get_bit_positions(start_bit_raw, bit_length)
                if bit_positions.__len__() > 0:
                    start_bit = bit_positions[0]
                else:
                    start_bit = start_bit_raw
            else:
                # 不需要转化为 LSB
                signal_format = Format.MOTOROLA_MSB
                start_bit = start_bit_raw
        else:  # Intel
            signal_format = Format.INTEL
            start_bit = start_bit_raw

        factor = float(match.group(5))
        offset = float(match.group(6))
        return SignalData(signal_format, can_id, "", signal_name, start_bit, bit_length, factor, offset)
