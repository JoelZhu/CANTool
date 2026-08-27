from typing import List

from PyQt5.QtWidgets import QMessageBox, QLabel

from core.MessageParser import MessageParser
from ui.page.Codec import Ui_CodecWidget
from ui.page.Home import Ui_MainWindow
from ui.window.SubWindow import SubWindow


class CodecWindow(SubWindow):
    def __init__(self, main_ui: Ui_MainWindow):
        super().__init__(main_ui)

        # 设置 ui 类
        self.ui = Ui_CodecWidget()
        self.ui.setupUi(self)

        # 连接按钮点击事件
        self.ui.btnParse.clicked.connect(self.on_parse)
        self.ui.btnGenerate.clicked.connect(self.on_generate)

    def mark_as_required(self) -> List[QLabel]:
        return [self.main_ui.labelFormat, self.main_ui.labelStartBit, self.main_ui.labelBitLength,
                self.main_ui.labelFactor, self.main_ui.labelOffset]

    def on_parse(self):
        try:
            self.__parse_inner__()
        except Exception as e:
            QMessageBox.critical(self, "Parse got exception.", str(e))

    def on_generate(self):
        try:
            self.__generate_inner__()
        except Exception as e:
            QMessageBox.critical(self, "Generate got exception.", str(e))

    def __parse_inner__(self):
        # 1. 获取矩阵信息
        parser, _, signal_data = self.get_and_check_if_parameters_legal()

        # 2. 获取报文数据
        raw_text = self.ui.editData.text().strip()
        if not raw_text:
            raise ValueError("CAN message can't be null.")
        # 替换逗号为空格，然后分割
        bytes_str = raw_text.replace(',', ' ')
        data_bytes = [int(x, 16) for x in bytes_str.split()]

        # 4. 解析
        result = MessageParser.parse_signal(parser, data_bytes, signal_data.start_bit, signal_data.bit_length,
                                            signal_data.factor, signal_data.offset)

        # 5. 显示结果
        self.ui.editRaw.setText(f"{result.raw_value} (0x{result.raw_value:X})")
        self.ui.editPhysical.setText(str(result.physical_value))

    def __generate_inner__(self):
        # 1. 获取矩阵信息
        parser, byte_length, signal_data = self.get_and_check_if_parameters_legal()

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
                message = MessageParser.generate_signal(parser, byte_length, signal_data.start_bit,
                                                        signal_data.bit_length, values)
            else:
                raise ValueError(f"Illegal raw value: {raw_text}.")
        else:
            physical_text = self.ui.spinPhysical.text().strip()
            if physical_text:
                physical_value = float(physical_text)
                values = {'physical': physical_value, 'factor': signal_data.factor, 'offset': signal_data.offset}
                message = MessageParser.generate_signal(parser, byte_length, signal_data.start_bit,
                                                        signal_data.bit_length, values)
            else:
                raise ValueError(f"Illegal physical value: {physical_text}.")

        # 3. 生成并且显示
        hex_str = ' '.join(f"{b:02X}" for b in message)
        self.ui.editResult.setText(hex_str)
