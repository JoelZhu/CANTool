from PyQt5.QtWidgets import QMessageBox

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

    def on_parse(self):
        try:
            # 1. 获取矩阵信息
            parser, start_bit, bit_length, _, factor, offset = self.get_matrix_information()

            # 2. 获取报文数据
            raw_text = self.ui.editData.text().strip()
            if not raw_text:
                raise ValueError("CAN message can't be empty.")
            # 替换逗号为空格，然后分割
            data_str = raw_text.replace(',', ' ')
            data_bytes = [int(x, 16) for x in data_str.split()]

            # 4. 解析
            result = MessageParser.parse_signal(parser, data_bytes, start_bit, bit_length, factor, offset)
            raw_value = result['raw']
            physical_value = result['physical']

            # 5. 显示结果
            self.ui.editRaw.setText(f"{raw_value} (0x{raw_value:X})")
            self.ui.editPhysical.setText(str(physical_value))

        except Exception as e:
            QMessageBox.critical(self, "Parse got exception.", str(e))
