import os
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QMainWindow

from core.MessageParser import MessageParser
from core.base.BaseParser import BaseParser
from core.base.Format import Format
from ui.Generator import Ui_GeneratorWidget
from ui.Home import Ui_MainWindow
from ui.Parser import Ui_MessageParser


# ---------- 解析器窗口类 ----------
class ParserWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 设置 ui 类
        self.ui = Ui_MessageParser()
        self.ui.setupUi(self)

        # 动态添加支持的报文格式
        parsers_dict = BaseParser.get_all_parsers()
        self.ui.comboFormat.clear()
        for key, value in parsers_dict.items():
            self.ui.comboFormat.addItem(key.value, value)

        # 连接按钮点击事件
        self.ui.btnParse.clicked.connect(self.on_parse)

    def on_parse(self):
        try:
            # 1. 获取格式
            parser = self.ui.comboFormat.currentData()
            if parser is None:
                raise ValueError("Parser can't be null.")

            # 2. 获取参数
            start_bit = self.ui.spinStartBit.value()
            bit_length = self.ui.spinBitLength.value()
            factor = self.ui.spinFactor.value()
            offset = self.ui.spinOffset.value()

            # 3. 获取报文数据
            raw_text = self.ui.editData.toPlainText().strip()
            if not raw_text:
                raise ValueError("CAN message can't be empty.")
            # 替换逗号为空格，然后分割
            data_str = raw_text.replace(',', ' ')
            data_bytes = [int(x, 16) for x in data_str.split()]

            # 4. 解析
            result = MessageParser.parse_signal(data_bytes, parser, start_bit, bit_length, factor, offset)
            raw_value = result['raw']
            physical_value = result['physical']

            # 5. 显示结果
            self.ui.editRaw.setText(f"{raw_value} (0x{raw_value:X})")
            self.ui.editPhysical.setText(str(physical_value))

        except Exception as e:
            QMessageBox.critical(self, "Parse got exception.", str(e))


# ---------- 生成器窗口类 ----------
class GeneratorWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 设置 ui 类
        self.ui = Ui_GeneratorWidget()
        self.ui.setupUi(self)


# ---------- 主窗口类 ----------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化解析器
        MessageParser.init_parser()

        # 添加图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 创建页面实例
        self.parser_page = ParserWindow()
        self.generator_page = GeneratorWindow()

        # 设置 UI 类
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # 添加到 TabWidget
        self.ui.tabWidget.addTab(self.parser_page, "Parser")
        self.ui.tabWidget.addTab(self.generator_page, "Generator")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 应用 Material 样式
    with open("ui/material_style.qss", "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
