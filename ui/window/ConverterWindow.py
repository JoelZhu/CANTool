from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QFileDialog
from can import ASCWriter

from core.ConvertHelper import ConvertHelper
from ui.dialog.ConvertDialog import ConvertDialog
from ui.page.Converter import Ui_ConverterWidget
from ui.page.Home import Ui_MainWindow
from ui.window.SubWindow import SubWindow


class ConverterWindow(SubWindow):
    def __init__(self, main_ui: Ui_MainWindow):
        super().__init__(main_ui)

        self.helper = ConvertHelper()

        self.thread = None
        self.parser = None
        self.result_dialog = None

        self.asc_writer: ASCWriter = None

        # 设置 ui 类
        self.ui = Ui_ConverterWidget()
        self.ui.setupUi(self)

        self.ui.browseButton.clicked.connect(self.on_browse_clicked)
        self.ui.convertButton.clicked.connect(self.on_conversion)

    def closeEvent(self, event):
        self.helper.on_close_event()
        event.accept()

    def on_browse_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select a BLF file", "", "BLF Files (*.blf);;All Files (*)"
        )
        if file_path:
            self.ui.filePathEdit.setText(file_path)

    def on_conversion(self):
        blf_path = self.__get_blf_path__()
        if not blf_path:
            return

        # 1. 关闭旧对话框（如果存在）
        if self.result_dialog:
            self.result_dialog.accept()
            self.result_dialog = None

        # 强制处理事件，确保所有清理信号已处理
        QCoreApplication.processEvents()
        # 创建对话框
        self.result_dialog = ConvertDialog(self)
        self.result_dialog.set_text("File converting...")
        self.result_dialog.prepare_blf_path(self.ui.filePathEdit.text().strip())
        self.result_dialog.show()
        # 注册回调
        self.helper.register_callbacks(progress=self.on_progressed, finished=self.on_finished, error=self.on_error)

        # 启用转化
        self.helper.start_conversion(blf_path, self.parser)

    def on_progressed(self, progress: int):
        self.__update_progress_text__(progress)

    def on_finished(self):
        if self.result_dialog:
            self.result_dialog.set_text("Succeed！", is_finished=True)

    def on_error(self, error_msg):
        if self.result_dialog:
            self.result_dialog.set_text(error_msg, is_finished=True, is_error=True)

    def __update_progress_text__(self, progress: int):
        if self.result_dialog:
            if progress < 0:
                self.result_dialog.set_text("Convert preparing...")
            else:
                self.result_dialog.set_text(f"Converting, progress: {progress}%")

    def __get_blf_path__(self) -> str:
        return self.ui.filePathEdit.text().strip()
