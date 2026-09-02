from typing import List

from PyQt5.QtWidgets import QWidget, QLabel

from core.entity.SignalData import SignalData
from ui.page.Home import Ui_MainWindow


def set_label_as_required(label: QLabel, visible: bool):
    if visible:
        label.setProperty("required", "true")
    else:
        label.setProperty("required", "false")
    # 强制刷新样式
    label.style().polish(label)


class SubWindow(QWidget):
    main_ui: Ui_MainWindow
    required_parameters: list

    def __init__(self, main_ui: Ui_MainWindow):
        super().__init__()
        self.main_ui = main_ui
        self.required_parameters = list()

    def on_window_changed(self):
        # 先全部不显示星标
        set_label_as_required(self.main_ui.labelFormat, False)
        set_label_as_required(self.main_ui.labelCanId, False)
        set_label_as_required(self.main_ui.labelBytes, False)
        set_label_as_required(self.main_ui.labelStartBit, False)
        set_label_as_required(self.main_ui.labelBitLength, False)
        set_label_as_required(self.main_ui.labelFactor, False)
        set_label_as_required(self.main_ui.labelOffset, False)
        # 针对性显示需要显示星标的
        requires = self.mark_as_required()
        self.required_parameters.clear()
        if requires:
            for required_label in self.mark_as_required():
                set_label_as_required(required_label, True)
                self.required_parameters.append(required_label)

    def mark_as_required(self) -> List[QLabel]:
        pass

    def change_label_to_required(self, label: QLabel):
        set_label_as_required(label, True)
        self.required_parameters.append(label)

    def change_label_to_optional(self, label: QLabel):
        set_label_as_required(label, False)
        if self.required_parameters.__contains__(label):
            self.required_parameters.remove(label)

    def get_and_check_if_parameters_legal(self) -> (int, SignalData):
        byte_length, signal_data = self.__get_matrix_information__()

        if self.main_ui.labelFormat in self.required_parameters:
            if not signal_data.format:
                raise ValueError("Format can't be null.")
        if self.main_ui.labelCanId in self.required_parameters:
            if not signal_data.can_id:
                raise ValueError("CAN Id can't be null.")
        if self.main_ui.labelBytes in self.required_parameters:
            if not byte_length:
                raise ValueError("Byte Length can't be null.")
        if self.main_ui.labelStartBit in self.required_parameters:
            if signal_data.start_bit is None:
                raise ValueError("Start Bit can't be null.")
        if self.main_ui.labelBitLength in self.required_parameters:
            if not signal_data.bit_length:
                raise ValueError("Bit Length can't be null.")
        if self.main_ui.labelFactor in self.required_parameters:
            if not signal_data.factor:
                raise ValueError("Factor can't be null.")
        if self.main_ui.labelOffset in self.required_parameters:
            if signal_data.offset is None:
                raise ValueError("Offset can't be null.")

        return byte_length, signal_data

    def update_parameters(self, data: SignalData):
        self.main_ui.comboFormat.setCurrentText(data.format.value)
        self.main_ui.editCanId.setText(hex(data.can_id)[2:].upper())
        self.main_ui.spinStartBit.setValue(data.start_bit)
        self.main_ui.spinBitLength.setValue(data.bit_length)
        self.main_ui.spinFactor.setValue(data.factor)
        self.main_ui.spinOffset.setValue(data.offset)

    def __get_matrix_information__(self) -> (int, SignalData):
        signal_format = self.main_ui.comboFormat.currentData()
        raw_can_id = self.main_ui.editCanId.text().upper().strip()
        if raw_can_id.startswith('0X'):
            raw_can_id = raw_can_id[2:]  # 去掉前两个字符
        can_id = raw_can_id.upper()
        byte_length = self.main_ui.spinByteLength.value()
        start_bit = self.main_ui.spinStartBit.value()
        bit_length = self.main_ui.spinBitLength.value()
        factor = self.main_ui.spinFactor.value()
        offset = self.main_ui.spinOffset.value()
        return byte_length, SignalData(signal_format, can_id, "", "", start_bit, bit_length, factor, offset)
