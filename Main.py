import os
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox

from core.MessageParser import MessageParser
from core.base.Format import Format
from ui.Parser import Ui_MessageParser


# ---------- 主窗口类 ----------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        MessageParser.init_parser()

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.ui = Ui_MessageParser()
        self.ui.setupUi(self)

        # 连接按钮点击事件
        self.ui.btnParse.clicked.connect(self.on_parse)

    def on_parse(self):
        try:
            # 1. 获取格式
            fmt_text = self.ui.comboFormat.currentText()
            if fmt_text == "Intel":
                fmt = Format.INTEL
            elif fmt_text == "Motorola LSB":
                fmt = Format.MOTOROLA_LSB
            elif fmt_text == "Motorola MSB":
                fmt = Format.MOTOROLA_MSB
            else:
                raise ValueError("未选择的格式")

            # 2. 获取参数
            start_bit = self.ui.spinStartBit.value()
            bit_length = self.ui.spinBitLength.value()
            factor = self.ui.spinFactor.value()
            offset = self.ui.spinOffset.value()

            # 3. 获取报文数据
            raw_text = self.ui.editData.text().strip()
            if not raw_text:
                raise ValueError("报文数据不能为空")
            # 替换逗号为空格，然后分割
            data_str = raw_text.replace(',', ' ')
            data_bytes = [int(x, 16) for x in data_str.split()]

            # 4. 解析
            result = MessageParser.parse_signal(data_bytes, fmt, start_bit, bit_length, factor, offset)
            raw_value = result['raw']
            physical_value = result['physical']

            # 5. 显示结果
            self.ui.editRaw.setText(f"{raw_value} (0x{raw_value:X})")
            self.ui.editPhysical.setText(str(physical_value))

        except Exception as e:
            QMessageBox.critical(self, "解析错误", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
