import os
from typing import Callable

from PyQt5.QtCore import QObject, pyqtSlot, QThread
from can import ASCWriter, Message

from core.BLFParser import BLFParser
from core.base.BaseParser import BaseParser


class ConvertHelper:
    def __init__(self):
        self.parser: BaseParser = None

        self.read_thread: QThread = None
        self.write_thread: QThread = None
        self.blf_parser = None
        self.writer_worker: ASCWriterWorker = None

        self.progress: Callable[[int], None] = None
        self.finished: Callable[[], None] = None
        self.error: Callable[[str], None] = None

    def on_close_event(self):
        if self.read_thread and self.read_thread.isRunning():
            self.read_thread.quit()
            if not self.read_thread.wait(2000):
                self.read_thread.terminate()
                self.read_thread.wait()

        if self.write_thread and self.write_thread.isRunning():
            self.write_thread.quit()
            if not self.write_thread.wait(2000):
                self.write_thread.terminate()
                self.write_thread.wait()

    def register_callbacks(self, progress: Callable[[int], None] = None, finished: Callable[[], None] = None,
                           error: Callable[[str], None] = None):
        self.progress = progress
        self.finished = finished
        self.error = error

    def prepare_analysing(self):
        # 1. 停止并等待旧线程结束
        if self.read_thread:
            # 断开所有信号连接，防止旧信号触发新对象
            try:
                self.read_thread.finished.disconnect()
            except TypeError:
                pass
            if self.read_thread.isRunning():
                self.read_thread.quit()
                if not self.read_thread.wait(2000):
                    self.read_thread.terminate()
                    self.read_thread.wait()
            # 手动释放，确保事件循环处理完删除事件
            self.read_thread.deleteLater()
            self.read_thread = None
        if self.write_thread:
            # 断开所有信号连接，防止旧信号触发新对象
            try:
                self.write_thread.finished.disconnect()
            except TypeError:
                pass
            if self.write_thread.isRunning():
                self.write_thread.quit()
                if not self.write_thread.wait(2000):
                    self.write_thread.terminate()
                    self.write_thread.wait()
            # 手动释放，确保事件循环处理完删除事件
            self.write_thread.deleteLater()
            self.write_thread = None
        if self.writer_worker:
            self.writer_worker.deleteLater()
            self.writer_worker = None

        # 2. 清除解析器未完成的操作
        if self.blf_parser:
            self.blf_parser.deleteLater()
            self.blf_parser = None

    def start_conversion(self, blf_path: str, parser: BaseParser):
        self.parser = parser

        self.read_thread = QThread()
        self.blf_parser = BLFParser(blf_path)
        self.blf_parser.moveToThread(self.read_thread)
        self.write_thread = QThread()
        self.writer_worker = ASCWriterWorker()
        self.writer_worker.moveToThread(self.write_thread)

        self.blf_parser.started.connect(lambda: self.writer_worker.open_file(blf_path))
        self.blf_parser.finished.connect(self.writer_worker.close_file)

        if self.progress:
            self.blf_parser.progress.connect(self.progress)
        if self.finished:
            self.blf_parser.finished.connect(self.finished)
        if self.error:
            self.blf_parser.error.connect(self.error)

        self.read_thread.started.connect(self.blf_parser.run)

        # 定义局部清理函数，确保引用正确
        def cleanup():
            if self.read_thread:
                self.read_thread.deleteLater()
                self.read_thread = None
            if self.blf_parser:
                self.blf_parser.deleteLater()
                self.blf_parser = None

        self.read_thread.finished.connect(cleanup)
        self.read_thread.start()


class ASCWriterWorker(QObject):
    def __init__(self):
        super().__init__()
        self.asc_writer = None

    @pyqtSlot(str)
    def open_file(self, blf_path: str):
        """根据 BLF 路径生成 ASC 文件路径并创建 ASCWriter"""
        base, _ = os.path.splitext(blf_path)
        self.asc_writer = ASCWriter(base + ".asc")

    @pyqtSlot(Message)
    def write_message(self, message: Message):
        """写入一条 CAN 消息"""
        if self.asc_writer:
            self.asc_writer.on_message_received(message)

    @pyqtSlot()
    def close_file(self):
        """关闭文件，释放资源"""
        if self.asc_writer:
            self.asc_writer.stop()
            self.asc_writer = None
