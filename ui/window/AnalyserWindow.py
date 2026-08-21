from PyQt5.QtWidgets import QMessageBox

from ui.page.Analyser import Ui_AnalyserWidget
from ui.page.Home import Ui_MainWindow
from ui.window.SubWindow import SubWindow


class AnalyserWindow(SubWindow):
    def __init__(self, main_ui: Ui_MainWindow):
        super().__init__(main_ui)

        # 设置 ui 类
        self.ui = Ui_AnalyserWidget()
        self.ui.setupUi(self)

        self.ui.btnRefresh.clicked.connect(self.refresh_matrix)

    def refresh_matrix(self):
        try:
            # 1. 获取矩阵信息
            parser, start_bit, bit_length, bytes_length, _, _ = self.get_matrix_information()

            # 3. 更新矩阵显示表格
            self.update_matrix_table(parser, start_bit, bit_length, bytes_length)

        except Exception as e:
            QMessageBox.critical(self, "Refresh got exception.", str(e))
