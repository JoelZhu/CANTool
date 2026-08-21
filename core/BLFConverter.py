import os

from PyQt5.QtCore import QObject, pyqtSignal
from can.io import BLFReader, ASCWriter

from core.Util import print_debug, print_error


class BLFConverter(QObject):
    started = pyqtSignal()
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, blf_path: str):
        super().__init__()
        base, _ = os.path.splitext(blf_path)
        self.blf_path = blf_path
        self.asc_path = base + ".asc"

    def run(self):
        try:
            self.started.emit()  # noqa
            total_messages = 0
            print_debug("To count message.")
            with BLFReader(self.blf_path) as reader:
                for _ in reader:  # noqa
                    # 先计算拥有多少条报文
                    total_messages += 1
            print_debug("Message count finished.")

            last_reported: int = -1
            written_message = 0
            print_debug("To write message.")
            with BLFReader(self.blf_path) as reader:
                with ASCWriter(self.asc_path) as writer:
                    for msg in reader:  # noqa
                        writer.on_message_received(msg)
                        written_message += 1
                        to_report = int(written_message * 100 / total_messages)
                        if to_report <= last_reported:
                            continue
                        last_reported = to_report
                        self.progress.emit(to_report)  # noqa

            print_debug("Message write finished.")
            self.finished.emit(self.asc_path)  # noqa
        except Exception as e:
            # 打印堆栈信息到控制台
            print_error(f"Convert BLF got exception: {str(e)}")
            self.error.emit(f"Failed: {str(e)}")  # noqa
