import os.path

from PyQt5.QtCore import QThread, Qt, QUrl, QCoreApplication
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog, QHBoxLayout

from core.BLFConverter import BLFConverter
from ui.page.Converter import Ui_ConverterWidget
from ui.page.Home import Ui_MainWindow
from ui.window.SubWindow import SubWindow


class ConverterWindow(SubWindow):
    def __init__(self, main_ui: Ui_MainWindow):
        super().__init__(main_ui)
        self.ui = Ui_ConverterWidget()
        self.ui.setupUi(self)

        self.ui.browseButton.clicked.connect(self.on_browse_clicked)
        self.ui.convertButton.clicked.connect(self.start_conversion)

        self.thread = None
        self.worker = None
        self.result_dialog = None

    def closeEvent(self, event):
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            if not self.thread.wait(2000):
                self.thread.terminate()
                self.thread.wait()
        event.accept()

    def on_browse_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select a BLF file", "", "BLF Files (*.blf);;All Files (*)"
        )
        if file_path:
            self.ui.filePathEdit.setText(file_path)

    def start_conversion(self):
        blf_path = self.ui.filePathEdit.text().strip()
        if not blf_path:
            return

        # 1. 关闭旧对话框（如果存在）
        if self.result_dialog:
            self.result_dialog.accept()
            self.result_dialog = None

        # 2. 停止并等待旧线程结束
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

        if self.worker:
            self.worker.deleteLater()
            self.worker = None

        # 强制处理事件，确保所有清理信号已处理
        QCoreApplication.processEvents()

        # ===== 创建新线程和对话框 =====
        self.result_dialog = ResultDialog(self)
        self.result_dialog.set_text("File converting...")
        self.result_dialog.prepare_blf_path(self.ui.filePathEdit.text().strip())
        self.result_dialog.show()

        self.thread = QThread()
        self.worker = BLFConverter(blf_path)
        self.worker.moveToThread(self.thread)

        # 连接信号
        self.worker.started.connect(lambda: self.update_progress_text(-1))
        self.worker.progress.connect(self.on_conversion_progressed)
        self.worker.finished.connect(self.on_conversion_finished)
        self.worker.error.connect(self.on_conversion_error)
        self.thread.started.connect(self.worker.run)

        # 定义局部清理函数，确保引用正确
        def cleanup():
            if self.thread:
                self.thread.deleteLater()
                self.thread = None
            if self.worker:
                self.worker.deleteLater()
                self.worker = None

        self.thread.finished.connect(cleanup)
        self.thread.start()

    def on_conversion_progressed(self, progress: int):
        self.update_progress_text(progress)

    def on_conversion_finished(self, output_path: str):
        if self.result_dialog:
            self.result_dialog.set_text("Succeed！", is_finished=True)

    def on_conversion_error(self, error_msg):
        if self.result_dialog:
            self.result_dialog.set_text(error_msg, is_finished=True, is_error=True)

    def update_progress_text(self, progress: int):
        if self.result_dialog:
            if progress < 0:
                self.result_dialog.set_text("Convert preparing...")
            else:
                self.result_dialog.set_text(f"Converting, progress: {progress}%")


class ResultDialog(QDialog):
    blf_path: str

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Convert Progress")
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)

        main_layout = QVBoxLayout(self)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.label)

        # 水平布局：用于按钮
        button_layout = QHBoxLayout()
        self.open_btn = QPushButton("Open")
        self.open_btn.setVisible(False)
        self.open_btn.clicked.connect(self.open_folder)
        button_layout.addWidget(self.open_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.setVisible(False)
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        # 将水平布局添加到主布局中
        main_layout.addLayout(button_layout)

        self.resize(350, 150)

    def prepare_blf_path(self, blf_path: str):
        self.blf_path = blf_path

    def set_text(self, text: str, is_finished: bool = False, is_error: bool = False):
        self.label.setText(text)
        if is_error:
            self.open_btn.setVisible(False)
            self.close_btn.setVisible(True)
        elif is_finished:
            self.open_btn.setVisible(True)
            self.close_btn.setVisible(True)
        else:
            self.open_btn.setVisible(False)
            self.close_btn.setVisible(False)

    def open_folder(self):
        if self.blf_path:
            # 打开文件夹
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(self.blf_path)))
