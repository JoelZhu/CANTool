import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QMainWindow, QHeaderView, QTableWidgetItem

from core.MessageParser import MessageParser
from core.base.BaseParser import BaseParser
from ui.Generator import Ui_GeneratorWidget
from ui.Home import Ui_MainWindow
from ui.Matrix import Ui_MatrixWidget
from ui.Parser import Ui_ParserWidget


class SubWindow(QWidget):
    main_ui: Ui_MainWindow

    def __init__(self, main_ui: Ui_MainWindow):
        super().__init__()
        self.main_ui = main_ui

    def get_matrix_information(self):
        parser = self.main_ui.comboFormat.currentData()
        start_bit = self.main_ui.spinStartBit.value()
        bit_length = self.main_ui.spinBitLength.value()
        return parser, start_bit, bit_length


# ---------- 解析器窗口类 ----------
class ParserWindow(SubWindow):
    def __init__(self, main_ui: Ui_MainWindow):
        super().__init__(main_ui)

        # 设置 ui 类
        self.ui = Ui_ParserWidget()
        self.ui.setupUi(self)

        # 连接按钮点击事件
        self.ui.btnParse.clicked.connect(self.on_parse)

    def on_parse(self):
        try:
            # 1. 获取矩阵信息
            parser, start_bit, bit_length = self.get_matrix_information()

            # 2. 获取报文数据
            raw_text = self.ui.editData.toPlainText().strip()
            if not raw_text:
                raise ValueError("CAN message can't be empty.")
            # 替换逗号为空格，然后分割
            data_str = raw_text.replace(',', ' ')
            data_bytes = [int(x, 16) for x in data_str.split()]

            # 3. 获取精度和偏移量
            factor = self.ui.spinFactor.value()
            offset = self.ui.spinOffset.value()

            # 4. 解析
            result = MessageParser.parse_signal(parser, data_bytes, start_bit, bit_length, factor, offset)
            raw_value = result['raw']
            physical_value = result['physical']

            # 5. 显示结果
            self.ui.editRaw.setText(f"{raw_value} (0x{raw_value:X})")
            self.ui.editPhysical.setText(str(physical_value))

        except Exception as e:
            QMessageBox.critical(self, "Parse got exception.", str(e))


# ---------- 生成器窗口类 ----------
class GeneratorWindow(SubWindow):
    def __init__(self, main_ui: Ui_MainWindow):
        super().__init__(main_ui)

        # 设置 ui 类
        self.ui = Ui_GeneratorWidget()
        self.ui.setupUi(self)

        # 连接按钮点击事件
        self.ui.btnGenerate.clicked.connect(self.on_generate)

    def on_generate(self):
        try:
            # 1. 获取矩阵信息
            parser, start_bit, bit_length = self.get_matrix_information()

            # 2. 获取报文数据
            raw_text = self.ui.spinRaw.text().strip()
            if not raw_text:
                return
            # 支持十进制或十六进制输入
            if raw_text.startswith("0x") or raw_text.startswith("0X"):
                raw_value = int(raw_text, 16)
            else:
                raw_value = int(raw_text)

            # 3. 获取字节长度
            bytes_length = int(self.ui.spinBytesLength.text().strip())

            # 4. 生成并且显示
            message = MessageParser.generate_signal(parser, raw_value, start_bit, bit_length, bytes_length)
            hex_str = ' '.join(f"{b:02X}" for b in message)
            self.ui.editResult.setPlainText(hex_str)

        except Exception as e:
            QMessageBox.critical(self, "Generate got exception.", str(e))


# ---------- 矩阵窗口类 ----------
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
            parser, start_bit, bit_length = self.get_matrix_information()

            # 2. 获取字节长度
            bytes_length = int(self.ui.spinBytesLength.text().strip())

            # 3. 更新矩阵显示表格
            self.update_table(parser, start_bit, bit_length, bytes_length)

        except Exception as e:
            QMessageBox.critical(self, "Refresh got exception.", str(e))

    def update_table(self, parser: BaseParser, start_bit: int, bit_length: int, bytes_length: int):
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


# ---------- 主窗口类 ----------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化解析器
        MessageParser.init_parser()

        # 添加图标
        icon_path = resource_path('app_icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 设置主界面类
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # 动态添加支持的报文格式
        parsers_dict = BaseParser.get_all_parsers()
        self.ui.comboFormat.clear()
        for key, value in parsers_dict.items():
            self.ui.comboFormat.addItem(key.value, value)

        # 创建页面实例
        self.parser_page = ParserWindow(self.ui)
        self.generator_page = GeneratorWindow(self.ui)
        self.matrix_page = MatrixWindow(self.ui)

        # 添加到 TabWidget
        self.ui.tabWidget.addTab(self.parser_page, "Parser")
        self.ui.tabWidget.addTab(self.generator_page, "Generator")
        self.ui.tabWidget.addTab(self.matrix_page, "Matrix")


def resource_path(relative_path):
    """获取资源文件的绝对路径，兼容开发环境和 PyInstaller 打包后"""
    if hasattr(sys, '_MEIPASS'):
        # 打包后，资源文件被解压到 _MEIPASS 目录
        base_path = sys._MEIPASS
    else:
        # 开发环境，使用当前文件所在目录
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 应用 Material 样式
    qss_path = resource_path('ui/material_style.qss')
    with open(qss_path, "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
