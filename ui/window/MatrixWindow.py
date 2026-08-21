from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHeaderView, QMessageBox, QTableWidgetItem

from core.MessageParser import MessageParser
from core.base.BaseParser import BaseParser
from ui.page.Home import Ui_MainWindow
from ui.page.Matrix import Ui_MatrixWidget
from ui.window.SubWindow import SubWindow


class MatrixWindow(SubWindow):
    def __init__(self, main_ui: Ui_MainWindow):
        super().__init__(main_ui)

        # 设置 ui 类
        self.ui = Ui_MatrixWidget()
        self.ui.setupUi(self)
        # 让所有列平分表格宽度
        self.ui.tableMatrix.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ui.tableMatrix.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ui.tableMatrix.setHorizontalHeaderLabels([str(f"Bit{i}") for i in range(7, -1, -1)])

        self.ui.btnRefresh.clicked.connect(self.refresh_matrix)

    def refresh_matrix(self):
        try:
            # 1. 获取矩阵信息
            parser, start_bit, bit_length, bytes_length, _, _ = self.get_matrix_information()

            # 3. 更新矩阵显示表格
            self.update_matrix_table(parser, start_bit, bit_length, bytes_length)

        except Exception as e:
            QMessageBox.critical(self, "Refresh got exception.", str(e))

    def update_matrix_table(self, parser: BaseParser, start_bit: int, bit_length: int, bytes_length: int):
        # 1. 获取需要显示的位信息
        positions = MessageParser.get_all_positions(parser, bytes_length, start_bit, bit_length)
        if any(pos < 0 for pos in positions):
            raise ValueError("Illegal matrix information.")

        # 2. 更新字节信息
        self.ui.tableMatrix.setRowCount(bytes_length)
        self.ui.tableMatrix.setVerticalHeaderLabels([f"Byte{i}" for i in range(bytes_length)])

        # 3. 刷新表格内容
        for row in range(bytes_length):
            for col in range(8):
                pos = row * 8 + (7 - col)
                item = QTableWidgetItem(f"Bit{pos}")

                if pos == start_bit:
                    item.setForeground(Qt.black)
                    item.setBackground(Qt.green)
                elif pos in positions:
                    item.setForeground(Qt.white)
                    item.setBackground(Qt.red)
                else:
                    item.setForeground(Qt.black)
                    item.setBackground(Qt.lightGray)
                item.setTextAlignment(Qt.AlignCenter)
                self.ui.tableMatrix.setItem(row, col, item)
