from typing import List

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QFileDialog, QHeaderView, QTableWidgetItem, QPushButton, QStyle, QWidget, QVBoxLayout, \
    QLabel, QTableWidget, QMessageBox

from ui.page.Analyser import Ui_AnalyserWidget
from ui.page.Home import Ui_MainWindow
from ui.window.SubWindow import SubWindow


class AnalyserWindow(SubWindow):
    def __init__(self, main_ui: Ui_MainWindow):
        super().__init__(main_ui)

        # 设置 ui 类
        self.ui = Ui_AnalyserWidget()
        self.ui.setupUi(self)
        self.setup_table()

        self.ui.addButton.clicked.connect(self.on_add_signal)
        self.ui.browseButton.clicked.connect(self.on_browse_clicked)

    def mark_as_required(self) -> List[QLabel]:
        return [self.main_ui.labelFormat, self.main_ui.labelCanId, self.main_ui.labelStartBit,
                self.main_ui.labelBitLength, self.main_ui.labelFactor, self.main_ui.labelOffset]

    def setup_table(self):
        # 信号关注表
        # 设置行高
        self.ui.tableWatch.verticalHeader().setDefaultSectionSize(32)

        # 固定宽度列
        self.ui.tableWatch.setColumnWidth(0, 80)  # CAN_ID
        self.ui.tableWatch.setColumnWidth(2, 80)  # StartBit
        self.ui.tableWatch.setColumnWidth(3, 80)  # BitLength
        self.ui.tableWatch.setColumnWidth(4, 100)  # Factor
        self.ui.tableWatch.setColumnWidth(5, 100)  # Offset
        self.ui.tableWatch.setColumnWidth(6, 80)  # Delete
        # 让 MessageName 拉伸，其余列固定
        header = self.ui.tableWatch.horizontalHeader()
        for col in range(7):
            if col == 1:
                header.setSectionResizeMode(col, QHeaderView.Stretch)
            else:
                header.setSectionResizeMode(col, QHeaderView.Fixed)
        # 禁止表格编辑
        self.ui.tableWatch.setEditTriggers(QTableWidget.NoEditTriggers)

        # 结果表
        self.ui.tableResult.setColumnWidth(0, 240)  # Timestamp
        self.ui.tableResult.setColumnWidth(2, 120)  # RawValue
        self.ui.tableResult.setColumnWidth(3, 120)  # PhysicalValue
        # 让 MessageName 拉伸，其余列固定
        header = self.ui.tableResult.horizontalHeader()
        for col in range(4):
            if col == 1:
                header.setSectionResizeMode(col, QHeaderView.Stretch)
            else:
                header.setSectionResizeMode(col, QHeaderView.Fixed)
        # 禁止表格编辑
        self.ui.tableResult.setEditTriggers(QTableWidget.NoEditTriggers)

    def on_add_signal(self):
        try:
            self.add_signal_inner()
        except Exception as e:
            QMessageBox.critical(self, "Add signal got exception.", str(e))

    def on_browse_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select a BLF file", "", "BLF Files (*.blf);;All Files (*)"
        )
        if file_path:
            self.ui.filePathEdit.setText(file_path)

    def add_signal_inner(self):
        # 1. 获取矩阵信息
        _, can_id, _, start_bit, bit_length, factor, offset = self.get_and_check_if_parameters_legal()
        signal_name = self.ui.editSignalName.text().strip()
        if not signal_name:
            raise ValueError("Signal Name can't be null.")

        # 2.1 新增一行
        row = self.ui.tableWatch.rowCount()
        self.ui.tableWatch.insertRow(row)
        # 2.2 填充新增行的数据
        self.ui.tableWatch.setItem(row, 0, QTableWidgetItem(f"0x{can_id}"))
        self.ui.tableWatch.setItem(row, 1, QTableWidgetItem(signal_name))
        self.ui.tableWatch.setItem(row, 2, QTableWidgetItem(str(start_bit)))
        self.ui.tableWatch.setItem(row, 3, QTableWidgetItem(str(bit_length)))
        self.ui.tableWatch.setItem(row, 4, QTableWidgetItem(str(factor)))
        self.ui.tableWatch.setItem(row, 5, QTableWidgetItem(str(offset)))
        # 2.3 显示删除按钮
        remove_icon = self.style().standardIcon(QStyle.SP_TrashIcon)

        remove_button = QPushButton()
        remove_button.setObjectName("removeButton")
        remove_button.setIcon(remove_icon)
        remove_button.setIconSize(QSize(16, 16))
        # 单独编写样式，因为全局样式的原因，只设置高和宽不会生效
        remove_button.setStyleSheet("""
            QPushButton#removeButton {
                min-height: 0px;
                max-height: 24px;
                height: 24px;
                padding: 0px;
                margin: 0px;
                border: none;
            }
        """)
        remove_button.setFixedSize(64, 24)
        remove_button.clicked.connect(lambda checked, r=row: self.remove_signal_inner(r))
        remove_container = QWidget()
        vbox = QVBoxLayout(remove_container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(remove_button, alignment=Qt.AlignCenter)
        self.ui.tableWatch.setCellWidget(row, 6, remove_container)

    def remove_signal_inner(self, row: int):
        self.ui.tableWatch.removeRow(row)
