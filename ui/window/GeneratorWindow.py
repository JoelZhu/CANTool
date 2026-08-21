from typing import List

from PyQt5.QtWidgets import QMessageBox, QLabel

from core.MessageParser import MessageParser
from ui.page.Generator import Ui_GeneratorWidget
from ui.page.Home import Ui_MainWindow
from ui.window.SubWindow import SubWindow


class GeneratorWindow(SubWindow):
    def __init__(self, main_ui: Ui_MainWindow):
        super().__init__(main_ui)

        # 设置 ui 类
        self.ui = Ui_GeneratorWidget()
        self.ui.setupUi(self)

        # 连接按钮点击事件
        self.ui.btnGenerate.clicked.connect(self.on_generate)

        self.ui.radioRaw.toggled.connect(self.on_raw_toggled)
        self.ui.radioPhysical.toggled.connect(self.on_physical_toggled)

    def mark_as_required(self) -> List[QLabel]:
        return [self.main_ui.labelFormat, self.main_ui.labelBytes, self.main_ui.labelStartBit,
                self.main_ui.labelBitLength]

    def on_generate(self):
        try:
            self.generate_inner()
        except Exception as e:
            QMessageBox.critical(self, "Generate got exception.", str(e))

    def on_raw_toggled(self):
        self.change_label_to_optional(self.main_ui.labelFactor)
        self.change_label_to_optional(self.main_ui.labelOffset)

    def on_physical_toggled(self):
        self.change_label_to_required(self.main_ui.labelFactor)
        self.change_label_to_required(self.main_ui.labelOffset)

    def generate_inner(self):
        # 1. 获取矩阵信息
        parser, _, byte_length, start_bit, bit_length, factor, offset = self.get_and_check_if_parameters_legal()

        # 2. 获取总线值（如果是物理值的话，需要转化为总线值）
        message: list
        is_raw_mode = self.ui.radioRaw.isChecked()
        if is_raw_mode:
            raw_text = self.ui.spinRaw.text().strip()
            if raw_text:
                if raw_text.startswith("0x") or raw_text.startswith("0X"):  # 支持十进制或十六进制输入
                    raw_value = int(raw_text, 16)
                else:
                    raw_value = int(raw_text)
                values = {'raw': raw_value}
                message = MessageParser.generate_signal(parser, byte_length, start_bit, bit_length, values)
            else:
                raise ValueError(f"Illegal raw value: {raw_text}.")
        else:
            physical_text = self.ui.spinPhysical.text().strip()
            if physical_text:
                physical_value = float(physical_text)
                values = {'physical': physical_value, 'factor': factor, 'offset': offset}
                message = MessageParser.generate_signal(parser, byte_length, start_bit, bit_length, values)
            else:
                raise ValueError(f"Illegal physical value: {physical_text}.")

        # 3. 生成并且显示
        hex_str = ' '.join(f"{b:02X}" for b in message)
        self.ui.editResult.setText(hex_str)
