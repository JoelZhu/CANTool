from typing import List

from PyQt5.QtWidgets import QMessageBox, QLabel

from core.MessageParser import MessageParser
from ui.page.Home import Ui_MainWindow
from ui.page.Parser import Ui_ParserWidget
from ui.window.SubWindow import SubWindow


class ParserWindow(SubWindow):
    def __init__(self, main_ui: Ui_MainWindow):
        super().__init__(main_ui)

        # 设置 ui 类
        self.ui = Ui_ParserWidget()
        self.ui.setupUi(self)

        # 连接按钮点击事件
        self.ui.btnParse.clicked.connect(self.on_parse)

    def mark_as_required(self) -> List[QLabel]:
        return [self.main_ui.labelFormat, self.main_ui.labelStartBit, self.main_ui.labelBitLength,
                self.main_ui.labelFactor, self.main_ui.labelOffset]

    def on_parse(self):
        try:
            self.parse_inner()
        except Exception as e:
            QMessageBox.critical(self, "Parse got exception.", str(e))

    def parse_inner(self):
        # 1. 获取矩阵信息
        parser, _, _, start_bit, bit_length, factor, offset = self.get_and_check_if_parameters_legal()

        # 2. 获取报文数据
        raw_text = self.ui.editData.text().strip()
        if not raw_text:
            raise ValueError("CAN message can't be null.")
        # 替换逗号为空格，然后分割
        bytes_str = raw_text.replace(',', ' ')
        byte_length = [int(x, 16) for x in bytes_str.split()]

        # 4. 解析
        result = MessageParser.parse_signal(parser, byte_length, start_bit, bit_length, factor, offset)
        raw_value = result['raw']
        physical_value = result['physical']

        # 5. 显示结果
        self.ui.editRaw.setText(f"{raw_value} (0x{raw_value:X})")
        self.ui.editPhysical.setText(str(physical_value))
