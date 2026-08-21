from PyQt5.QtCore import QObject, pyqtSignal
from can import Message
from can.io import BLFReader

from core.Util import print_debug, print_error


class BLFParser(QObject):
    started = pyqtSignal()
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    before_parsing = pyqtSignal()
    on_parsing = pyqtSignal(Message)

    def __init__(self, blf_path: str):
        super().__init__()
        self.blf_path = blf_path

    def run(self):
        try:
            self.started.emit()  # noqa
            total_messages = 0
            print_debug("To count message.")
            first_reader = BLFReader(self.blf_path)
            for _ in first_reader:  # noqa
                # 先计算拥有多少条报文
                total_messages += 1
            print_debug("Message count finished.")

            # 回调解析之前的状态
            self.before_parsing.emit()  # noqa

            last_reported: int = -1
            parsed_message_count = 0
            print_debug("To write message.")
            actual_reader = BLFReader(self.blf_path)
            for each_message in actual_reader:  # noqa
                # 回调每一个消息
                self.on_parsing.emit(each_message)  # noqa

                parsed_message_count += 1
                to_report = int(parsed_message_count * 100 / total_messages)
                if to_report <= last_reported:
                    continue
                last_reported = to_report
                self.progress.emit(to_report)  # noqa

            print_debug("Message parse finished.")
            self.finished.emit()  # noqa
        except Exception as e:
            # 打印堆栈信息到控制台
            print_error(f"Convert BLF got exception: {str(e)}")
            self.error.emit(f"Failed: {str(e)}")  # noqa
