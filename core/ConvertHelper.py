import os
from typing import Callable

from PyQt5.QtCore import QObject, pyqtSlot, QThread, pyqtSignal
from can import ASCWriter, Message

from core.Util import print_debug, print_error
from core.base.BaseParser import BaseParser
from core.parser.BLFParser import BLFParser


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
        # 停止读线程和写线程，但不删除对象（由 finished 信号负责清理）
        self._stop_thread(self.read_thread)
        self._stop_thread(self.write_thread)

    def register_callbacks(self, progress: Callable[[int], None] = None, finished: Callable[[], None] = None,
                           error: Callable[[str], None] = None):
        self.progress = progress
        self.finished = finished
        self.error = error

    def prepare_analysing(self):
        # 停止旧线程，但不手动删除对象，也不断开 finished 信号
        # 线程结束后会自动触发清理槽，将引用置为 None
        self._stop_thread(self.read_thread)
        self._stop_thread(self.write_thread)

        # 此时可能线程尚未完全清理，但 start_conversion 会创建新线程并覆盖引用
        # 由于清理槽使用闭包捕获旧对象，不会影响新线程

    def start_conversion(self, blf_path: str, parser: BaseParser):
        self.parser = parser

        # 先确保旧线程已停止（但不清除引用，避免竞态）
        self.prepare_analysing()

        # 创建新线程和对象
        read_thread = QThread()
        read_thread.setObjectName("ReadThread")
        blf_parser = BLFParser(blf_path)
        blf_parser.moveToThread(read_thread)

        write_thread = QThread()
        write_thread.setObjectName("WriteThread")
        writer_worker = ASCWriterWorker()
        writer_worker.moveToThread(write_thread)

        # 保存引用
        self.read_thread = read_thread
        self.write_thread = write_thread
        self.blf_parser = blf_parser
        self.writer_worker = writer_worker

        # 信号连接
        blf_parser.started.connect(lambda: writer_worker.open_file(blf_path))
        blf_parser.on_parsing.connect(writer_worker.write_message)
        blf_parser.finished.connect(writer_worker.close_file)

        if self.progress:
            blf_parser.progress.connect(self.progress)
        if self.error:
            blf_parser.error.connect(self.error)

        # 文件关闭完成后通知外部 finished 回调
        writer_worker.closed.connect(self.__on_worker_closed__)  # noqa

        # 读线程启动
        read_thread.started.connect(blf_parser.run)

        def cleanup_read_thread():
            # 只清理属于这个线程的对象
            if self.read_thread is read_thread:
                self.read_thread = None
            if self.blf_parser is blf_parser:
                self.blf_parser = None
            read_thread.deleteLater()
            blf_parser.deleteLater()

        def cleanup_write_thread():
            if self.write_thread is write_thread:
                self.write_thread = None
            if self.writer_worker is writer_worker:
                self.writer_worker = None
            write_thread.deleteLater()
            writer_worker.deleteLater()

        read_thread.finished.connect(cleanup_read_thread)
        write_thread.finished.connect(cleanup_write_thread)

        # 启动线程
        read_thread.start()
        write_thread.start()

    def _stop_thread(self, thread: QThread, timeout_ms: int = 3000):
        """请求线程退出并等待，返回是否成功停止"""
        if not thread or not thread.isRunning():
            return True
        thread.quit()
        thread.requestInterruption()  # 若 run 中检查了中断标志则生效
        if thread.wait(timeout_ms):
            return True
        print_error(f"Thread {thread.objectName()} did not stop in time, forcing termination")
        thread.terminate()
        thread.wait()  # 强制终止后必须等待
        return False

    def __on_worker_closed__(self):
        # 文件已关闭，触发外部回调
        if self.finished:
            self.finished()


class ASCWriterWorker(QObject):
    closed = pyqtSignal()  # 文件关闭完成信号

    def __init__(self):
        super().__init__()
        self.asc_writer = None
        self.on_parse_error_called: bool = False

    @pyqtSlot(str)
    def open_file(self, blf_path: str):
        base, _ = os.path.splitext(blf_path)
        asc_file = base + ".asc"
        self.asc_writer = ASCWriter(asc_file)
        print_debug(f"To generate asc path: {asc_file}.")

    @pyqtSlot(Message)
    def write_message(self, message: Message):
        if self.asc_writer:
            self.asc_writer.on_message_received(message)
        else:
            if not self.on_parse_error_called:
                print_error(f"ASC file not exists.")
                self.on_parse_error_called = True

    @pyqtSlot()
    def close_file(self):
        if self.asc_writer:
            self.asc_writer.stop()
            self.asc_writer = None
            print_debug("ASC writer released.")
        else:
            print_error("ASC file not exists, can't release it.")
        # 发射关闭完成信号
        self.closed.emit()  # noqa
        # 退出写线程的事件循环，使其随后结束
        QThread.currentThread().quit()
