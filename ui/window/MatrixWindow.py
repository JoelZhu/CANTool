from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHeaderView, QMessageBox, QTableWidgetItem, QLabel, QTableWidget

from core.format.Format import Format
from core.parser.MessageParser import MessageParser
from ui.page.Home import Ui_MainWindow
from ui.page.Matrix import Ui_MatrixWidget
from ui.window.SubWindow import SubWindow


class MatrixWindow(SubWindow):
    def __init__(self, main_ui: Ui_MainWindow):
        super().__init__(main_ui)

        # 设置 ui 类
        self.ui = Ui_MatrixWidget()
        self.ui.setupUi(self)

        # 设置行高
        self.ui.tableMatrix.verticalHeader().setDefaultSectionSize(36)
        # 让所有列平分表格宽度
        self.ui.tableMatrix.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ui.tableMatrix.setHorizontalHeaderLabels([str(f"Bit{i}") for i in range(7, -1, -1)])
        # 禁止表格编辑
        self.ui.tableMatrix.setEditTriggers(QTableWidget.NoEditTriggers)

        self.ui.buttonRefresh.clicked.connect(self.on_refresh_matrix)

    def mark_as_required(self) -> List[QLabel]:
        return [self.main_ui.labelFormat, self.main_ui.labelBytes, self.main_ui.labelStartBit,
                self.main_ui.labelBitLength]

    def on_refresh_matrix(self):
        try:
            self.__refresh_matrix_inner__()
        except Exception as e:
            QMessageBox.critical(self, "Refresh got exception.", str(e))

    def __refresh_matrix_inner__(self):
        # 1. 获取矩阵信息
        byte_length, signal_data = self.get_and_check_if_parameters_legal()

        # 2. 更新矩阵显示表格
        self.__update_matrix_table__(signal_data.format, byte_length, signal_data.start_bit, signal_data.bit_length)

    def __update_matrix_table__(self, fmt: Format, byte_length: int, start_bit: int, bit_length: int):
        # 1. 获取需要显示的位信息
        positions = MessageParser.get_all_positions(fmt, byte_length, start_bit, bit_length)
        if any(pos < 0 for pos in positions):
            raise ValueError("Illegal matrix information.")

        # 2. 更新字节信息
        self.ui.tableMatrix.setRowCount(byte_length)
        self.ui.tableMatrix.setVerticalHeaderLabels([f"Byte{i}" for i in range(byte_length)])

        # 3. 刷新表格内容
        for row in range(byte_length):
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
