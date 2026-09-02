from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Callable, List

from PyQt5.QtCore import QThread, Qt
from can import Message

from core.parser.BLFParser import BLFParser
from core.parser.MessageParser import MessageParser
from core.Util import print_warn, print_debug
from core.base.BaseParser import BaseParser
from core.entity.SignalValue import SignalValue

BEIJING_TIMEZONE = timezone(timedelta(hours=8))


@dataclass
class AnalyseResult:
    timestamp: str
    channel: str
    direction: str
    signal_name: str
    raw_display: str
    physical_display: str


class AnalyseHelper:
    def __init__(self):
        self.watching_map: {} = None

        self.thread: QThread = None
        self.blf_parser = None

        self.started: Callable[[], None] = None
        self.finished: Callable[[List[AnalyseResult]], None] = None
        self.error: Callable[[str], None] = None

        self.analyse_results: List[AnalyseResult] = list()
        self.last_values = {}  # 用于记录每个信号的上一个值

    def on_close_event(self):
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            if not self.thread.wait(2000):
                self.thread.terminate()
                self.thread.wait()

    def register_callbacks(self, started: Callable[[], None] = None,
                           finished: Callable[[List[AnalyseResult]], None] = None, error: Callable[[str], None] = None):
        self.started = started
        self.finished = finished
        self.error = error

    def prepare_analysing(self):
        # 1. 停止并等待旧线程结束
        if self.thread:
            # 断开所有信号连接，防止旧信号触发新对象
            try:
                self.thread.finished.disconnect()
            except TypeError:
                pass
            if self.thread.isRunning():
                self.thread.quit()
                if not self.thread.wait(2000):
                    self.thread.terminate()
                    self.thread.wait()
            # 手动释放，确保事件循环处理完删除事件
            self.thread.deleteLater()
            self.thread = None

        # 2. 清除解析器未完成的操作
        if self.blf_parser:
            self.blf_parser.deleteLater()
            self.blf_parser = None

    def start_analysing(self, blf_path: str, watching_map: {}):
        self.watching_map = watching_map
        self.analyse_results.clear()
        self.last_values.clear()

        self.thread = QThread()
        self.blf_parser = BLFParser(blf_path, need_progress=False)
        self.blf_parser.moveToThread(self.thread)

        self.blf_parser.on_parsing.connect(self.on_parsing, Qt.DirectConnection)
        if self.started:
            self.blf_parser.started.connect(self.on_started)
        if self.finished:
            self.blf_parser.finished.connect(self.on_finished)
        if self.error:
            self.blf_parser.error.connect(self.on_error)

        self.thread.started.connect(self.blf_parser.run)

        # 定义局部清理函数，确保引用正确
        def cleanup():
            if self.thread:
                self.thread.deleteLater()
                self.thread = None
            if self.blf_parser:
                self.blf_parser.deleteLater()
                self.blf_parser = None

        self.thread.finished.connect(cleanup)
        self.thread.start()

    def on_started(self):
        self.started()

    def on_parsing(self, can_message: Message):
        can_id = can_message.arbitration_id
        can_channel = str(can_message.channel)
        for direction, signal in self.watching_map.get(can_id, []):
            if not signal:
                return

            try:
                data_bytes = list(can_message.data)
                start_bit = signal.start_bit
                bit_length = signal.bit_length
                factor = signal.factor
                offset = signal.offset
                result = MessageParser.parse_signal(signal.format, data_bytes, start_bit, bit_length, factor, offset)
            except ValueError as e:
                # 信号定义超出数据长度，可记录日志或跳过
                print_warn(f"Warning: {e}")
                continue

            self.__on_parsed__(can_message.timestamp, direction, can_channel, signal.signal_name, result)

    def on_finished(self):
        print_debug(f"Analyse finished.")
        self.finished(self.analyse_results)

    def on_error(self, error: str):
        self.error(error)

    def __on_parsed__(self, timestamp: float, direction: str, channel: str, signal_name: str, values: SignalValue):
        key = (direction, signal_name, channel)
        if key in self.last_values:
            old_raw, old_physical = self.last_values[key]
            new_raw, new_physical = values.raw_value, values.physical_value

            # 判断 raw 值是否变化（可根据需求改为判断 physical 值）
            if new_raw == old_raw:
                return  # 值未变化，直接忽略

            # 值发生变化，构造显示文本
            raw_display = f"{old_raw}->{new_raw}"
            physical_display = f"{old_physical:.6f}->{new_physical:.6f}"
        else:
            # 第一次出现，直接显示当前值
            raw_display = str(values.raw_value)
            physical_display = f"{values.physical_value:.6f}"
        # 更新记录
        self.last_values[key] = (values.raw_value, values.physical_value)

        self.analyse_results.append(
            AnalyseResult(self.__timestamp_to_beijing_str__(timestamp), channel, direction, signal_name,
                          raw_display, physical_display))

    def __timestamp_to_beijing_str__(self, timestamp: float, fmt: str = "%Y-%m-%d %H:%M:%S.%f") -> str:
        # 将时间戳转为 UTC 时间的 datetime 对象
        dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        # 转换为北京时区
        dt_beijing = dt_utc.astimezone(BEIJING_TIMEZONE)
        # 格式化字符串
        return dt_beijing.strftime(fmt)
