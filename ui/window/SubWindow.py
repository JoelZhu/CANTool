from PyQt5.QtWidgets import QWidget

from ui.page.Home import Ui_MainWindow


class SubWindow(QWidget):
    main_ui: Ui_MainWindow

    def __init__(self, main_ui: Ui_MainWindow):
        super().__init__()
        self.main_ui = main_ui

    def get_matrix_information(self):
        parser = self.main_ui.comboFormat.currentData()
        start_bit = self.main_ui.spinStartBit.value()
        bit_length = self.main_ui.spinBitLength.value()
        bytes_length = self.main_ui.spinBytesLength.value()
        factor = self.main_ui.spinFactor.value()
        offset = self.main_ui.spinOffset.value()
        return parser, start_bit, bit_length, bytes_length, factor, offset
