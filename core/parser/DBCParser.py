import os
import re
from dataclasses import dataclass
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

SETTINGS_KEY_PATH = "path"
SETTINGS_KEY_ALIAS = "alias"


@dataclass
class DBCInformation:
    alias: str  # 别名
    data: SignalData  # 信号


@dataclass
class DBCStoredEntry:
    path: str
    alias: str = ""


class DBCParser:
    loaded_dbc: Dict[str, List[DBCInformation]] = dict()
    is_lsb_first_in_motorola: bool = True

    dbc_change_callback: Callable[[], None] = None

    @classmethod
    def init_parser(cls):
        try:
            cls.is_lsb_first_in_motorola = int(settings.value(KEY_LSB_FIRST, VALUE_LSB_FIRST)) == VALUE_LSB_FIRST
        except Exception as exception:
            cls.is_lsb_first_in_motorola = True
            print_error(f"Got LSB first failed, {str(exception)}")

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
    def load_dbc(cls, file_path: str, file_alias: str = None) -> bool:
        """
        解析 DBC 文件，提取所有报文中的信号信息。
        :param file_path: DBC 文件路径
        :param file_alias: DBC 文件的别名（可选）
        :return 加载结果
        """
        signals: List[DBCInformation] = []
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
                    alias = file_alias if file_alias else ""
                    signals.append(DBCInformation(alias, signal))

        load_result = False
        if signals.__len__() > 0:
            print_debug(f"DBC file: {file_path} (alias: {file_alias}) loaded successfully.")
            cls.loaded_dbc[file_path] = signals
            entries = cls.query_stored_dbc_files()
            if not any(entry.path == file_path for entry in entries):
                entries.append(DBCStoredEntry(path=file_path, alias=file_alias if file_alias else ""))
                cls.__write_entries__(entries)
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
        except Exception as exception:
            print_error(f"DBC file: {file_path} not exists, unload failed: {str(exception)}.")

        entries = cls.query_stored_dbc_files()
        new_entries = [entry for entry in entries if entry.path != file_path]
        if len(new_entries) != len(entries):
            cls.__write_entries__(new_entries)
            # 通知监听者 DBC 发生了变化
            if cls.dbc_change_callback:
                cls.dbc_change_callback()

    @classmethod
    def query_stored_dbc_files(cls) -> List[DBCStoredEntry]:
        return cls.__read_entries__()

    @classmethod
    def query_all_loaded_signals(cls) -> List[DBCInformation]:
        all_signals = []
        for signal_list in cls.loaded_dbc.values():
            all_signals.extend(signal_list)
        return all_signals

    @classmethod
    def find_signal_from_loaded_dbc(cls, searching_signal_name: str) -> List[DBCInformation]:
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
                if search_lower in signal.data.signal_name.lower():
                    results.append(signal)
                    if len(results) >= 5:
                        return results[:5]
        return results[:5]

    @classmethod
    def __load_all_dbc__(cls, reset: bool = False):
        entries = cls.query_stored_dbc_files()

        if reset:
            cls.loaded_dbc.clear()

        print_debug(f"To load all loaded DBC files: {entries}.")
        for entry in entries:
            cls.load_dbc(entry.path, entry.alias or None)

    @classmethod
    def __clean_line__(cls, line: str) -> str:
        # 去除行内注释和首尾空白，返回处理后的字符串（可能为空）
        if '//' in line:
            line = line.split('//', 1)[0]
        return line.strip()

    @classmethod
    def __read_entries__(cls) -> List[DBCStoredEntry]:
        """读取存储，自动迁移旧格式。"""

        # 1. 先探测旧格式：QSettings 里如果还是 str，说明是旧数据
        raw = settings.value(KEY_DBC_PATHS, None)
        if isinstance(raw, str) and raw.strip():
            old_paths = [old_path for old_path in raw.split(DBC_PATH_SPLITER) if old_path.strip()]
            entries = [DBCStoredEntry(path=old_path.strip(), alias="") for old_path in old_paths]
            # 清掉旧键，写回新数组格式
            settings.remove(KEY_DBC_PATHS)
            cls.__write_entries__(entries)
            print_debug(f"Migrate DBC paths to array format: {entries}")
            return entries

        # 2. 新格式：读数组
        entries: List[DBCStoredEntry] = []
        size = settings.beginReadArray(KEY_DBC_PATHS)
        try:
            for index in range(size):
                settings.setArrayIndex(index)
                path = settings.value(SETTINGS_KEY_PATH, "")
                alias = settings.value(SETTINGS_KEY_ALIAS, "")
                if path:
                    entries.append(DBCStoredEntry(path=str(path), alias=str(alias)))
        finally:
            settings.endArray()
        return entries

    @classmethod
    def __write_entries__(cls, entries: List[DBCStoredEntry]) -> None:
        """写入 QSettings 数组格式。"""
        settings.remove(KEY_DBC_PATHS)  # 先清空，避免残留
        settings.beginWriteArray(KEY_DBC_PATHS)
        try:
            for index, entry in enumerate(entries):
                settings.setArrayIndex(index)
                settings.setValue(SETTINGS_KEY_PATH, entry.path)
                settings.setValue(SETTINGS_KEY_ALIAS, entry.alias)
        finally:
            settings.endArray()

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
