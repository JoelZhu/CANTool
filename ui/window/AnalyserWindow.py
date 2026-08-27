from typing import List, Tuple

from PyQt5.QtCore import Qt, QSize, QCoreApplication
from PyQt5.QtWidgets import QFileDialog, QHeaderView, QTableWidgetItem, QPushButton, QStyle, QWidget, QVBoxLayout, \
    QLabel, QTableWidget, QMessageBox, QCheckBox

from core.AnalyseHelper import AnalyseHelper, AnalyseResult
from core.entity.SignalData import SignalData
from ui.dialog.AnalyseDialog import AnalyseDialog
from ui.page.Analyser import Ui_AnalyserWidget
from ui.page.Home import Ui_MainWindow
from ui.window.SubWindow import SubWindow

INDEX_WATCHING_CAN_ID = 0
INDEX_WATCHING_DIRECTION = 1
INDEX_WATCHING_SIGNAL_NAME = 2
INDEX_WATCHING_START_BIT = 3
INDEX_WATCHING_BIT_LENGTH = 4
INDEX_WATCHING_FACTOR = 5
INDEX_WATCHING_OFFSET = 6
INDEX_WATCHING_REMOVE = 7
INDEX_WATCHING_SUM = INDEX_WATCHING_REMOVE + 1

INDEX_RESULT_TIMESTAMP = 0
INDEX_RESULT_CHANNEL = 1
INDEX_RESULT_DIRECTION = 2
INDEX_RESULT_SIGNAL_NAME = 3
INDEX_RESULT_RAW_VALUE = 4
INDEX_RESULT_PHYSICAL_VALUE = 5
INDEX_RESULT_SUM = INDEX_RESULT_PHYSICAL_VALUE + 1


class AnalyserWindow(SubWindow):
    def __init__(self, main_ui: Ui_MainWindow):
        super().__init__(main_ui)

        self.helper = AnalyseHelper()

        self.result_dialog = None
        self.channel_checkboxes = []

        self._watching_map = {}  # can_id -> list[str, SignalData]
        self._analyse_result: List[AnalyseResult] = list()

        # 设置 ui 类
        self.ui = Ui_AnalyserWidget()
        self.ui.setupUi(self)
        self.setup_table()

        self.ui.addButton.clicked.connect(self.on_add_signal)
        self.ui.browseButton.clicked.connect(self.on_browse_clicked)
        self.ui.analyseButton.clicked.connect(self.on_analyse)

    def closeEvent(self, event):
        self.helper.on_close_event()
        event.accept()

    def mark_as_required(self) -> List[QLabel]:
        return [self.main_ui.labelFormat, self.main_ui.labelCanId, self.main_ui.labelStartBit,
                self.main_ui.labelBitLength, self.main_ui.labelFactor, self.main_ui.labelOffset]

    def setup_table(self):
        # 信号关注表
        # 设置行高
        self.ui.tableWatch.verticalHeader().setDefaultSectionSize(32)
        # 固定宽度列
        self.ui.tableWatch.setColumnWidth(INDEX_WATCHING_CAN_ID, 80)  # CAN_ID
        self.ui.tableWatch.setColumnWidth(INDEX_WATCHING_DIRECTION, 80)  # Direction
        self.ui.tableWatch.setColumnWidth(INDEX_WATCHING_START_BIT, 80)  # StartBit
        self.ui.tableWatch.setColumnWidth(INDEX_WATCHING_BIT_LENGTH, 80)  # BitLength
        self.ui.tableWatch.setColumnWidth(INDEX_WATCHING_FACTOR, 120)  # Factor
        self.ui.tableWatch.setColumnWidth(INDEX_WATCHING_OFFSET, 120)  # Offset
        self.ui.tableWatch.setColumnWidth(INDEX_WATCHING_REMOVE, 80)  # RemoveButton
        # 让 SignalName 拉伸，其余列固定
        header = self.ui.tableWatch.horizontalHeader()
        for col in range(INDEX_WATCHING_SUM):
            if col == INDEX_WATCHING_SIGNAL_NAME:
                header.setSectionResizeMode(col, QHeaderView.Stretch)
            else:
                header.setSectionResizeMode(col, QHeaderView.Fixed)
        # 禁止表格编辑
        self.ui.tableWatch.setEditTriggers(QTableWidget.NoEditTriggers)

        # 结果表
        self.ui.tableResult.setColumnWidth(INDEX_RESULT_TIMESTAMP, 200)  # Timestamp
        self.ui.tableResult.setColumnWidth(INDEX_RESULT_CHANNEL, 60)  # Channel
        self.ui.tableResult.setColumnWidth(INDEX_RESULT_DIRECTION, 80)  # Direction
        self.ui.tableResult.setColumnWidth(INDEX_RESULT_RAW_VALUE, 120)  # RawValue
        self.ui.tableResult.setColumnWidth(INDEX_RESULT_PHYSICAL_VALUE, 180)  # PhysicalValue
        # 让 SignalName 拉伸，其余列固定
        header = self.ui.tableResult.horizontalHeader()
        for col in range(INDEX_RESULT_SUM):
            if col == INDEX_RESULT_SIGNAL_NAME:
                header.setSectionResizeMode(col, QHeaderView.Stretch)
            else:
                header.setSectionResizeMode(col, QHeaderView.Fixed)
        # 禁止表格编辑
        self.ui.tableResult.setEditTriggers(QTableWidget.NoEditTriggers)

    def on_add_signal(self):
        try:
            self.__add_signal_inner__()
        except Exception as e:
            QMessageBox.critical(self, "Add signal got exception.", str(e))

    def on_browse_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select a BLF file", "", "BLF Files (*.blf);;All Files (*)"
        )
        if file_path:
            self.ui.filePathEdit.setText(file_path)

    def on_analyse(self):
        blf_path = self.__get_blf_path__()
        if not blf_path:
            return

        # 1. 关闭旧对话框（如果存在）
        if self.result_dialog:
            self.result_dialog.accept()
            self.result_dialog = None

        # 2. 解析前的准备
        self.helper.prepare_analysing()
        # 强制处理事件，确保所有清理信号已处理
        QCoreApplication.processEvents()
        # 创建对话框
        self.result_dialog = AnalyseDialog(self)
        self.result_dialog.set_text("File analysing...")
        self.result_dialog.prepare_blf_path(self.ui.filePathEdit.text().strip())
        self.result_dialog.show()
        # 注册回调
        self.helper.register_callbacks(started=self.on_start, finished=self.on_finished, error=self.on_error)

        # 3. 启用分析
        parser, _, _ = self.get_and_check_if_parameters_legal()
        self.helper.start_analysing(blf_path, parser, self._watching_map)

    def on_channel_filter_changed(self, state):
        self.__apply_channel_filter__()

    def on_start(self):
        self.__update_progress_text__()

        watching_list = self.__get_watching_list__()
        self._watching_map.clear()
        for (direction, signal) in watching_list:
            self._watching_map.setdefault(signal.can_id, []).append((direction, signal))

        self.ui.tableResult.setRowCount(0)

    def on_finished(self, results: List[AnalyseResult]):
        self._analyse_result.clear()
        self._analyse_result.extend(results)
        self.__update_channel_filter_options__(results)

        self.__refresh_result_table__(self._analyse_result)

        if self.result_dialog:
            self.result_dialog.set_text("Succeed！", is_finished=True)

    def on_error(self, error_msg):
        if self.result_dialog:
            self.result_dialog.set_text(error_msg, is_finished=True, is_error=True)

    def __add_signal_inner__(self):
        # 1.1 获取矩阵信息
        _, _, signal_data = self.get_and_check_if_parameters_legal()
        # 1.2 获取信号补充信息
        signal_name = self.ui.editSignalName.text().strip()
        if not signal_name:
            raise ValueError("Signal Name can't be null.")
        direction = self.ui.comboDirection.currentText()

        # 2.1 新增一行
        row = self.ui.tableWatch.rowCount()
        self.ui.tableWatch.insertRow(row)
        # 2.2 填充新增行的数据
        self.ui.tableWatch.setItem(row, INDEX_WATCHING_CAN_ID, QTableWidgetItem(f"0x{signal_data.can_id}"))
        self.ui.tableWatch.setItem(row, INDEX_WATCHING_DIRECTION, QTableWidgetItem(direction))
        self.ui.tableWatch.setItem(row, INDEX_WATCHING_SIGNAL_NAME, QTableWidgetItem(signal_name))
        self.ui.tableWatch.setItem(row, INDEX_WATCHING_START_BIT, QTableWidgetItem(str(signal_data.start_bit)))
        self.ui.tableWatch.setItem(row, INDEX_WATCHING_BIT_LENGTH, QTableWidgetItem(str(signal_data.bit_length)))
        self.ui.tableWatch.setItem(row, INDEX_WATCHING_FACTOR, QTableWidgetItem(str(signal_data.factor)))
        self.ui.tableWatch.setItem(row, INDEX_WATCHING_OFFSET, QTableWidgetItem(str(signal_data.offset)))
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
        remove_button.clicked.connect(lambda checked, r=row: self.__remove_signal_inner__(r))
        remove_container = QWidget()
        vbox = QVBoxLayout(remove_container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(remove_button, alignment=Qt.AlignCenter)
        self.ui.tableWatch.setCellWidget(row, INDEX_WATCHING_REMOVE, remove_container)

    def __remove_signal_inner__(self, row: int):
        self.ui.tableWatch.removeRow(row)

    def __apply_channel_filter__(self):
        selected_channels = self.__get_selected_channels__()
        if not selected_channels:
            filtered_results = []
        else:
            filtered_results = [result for result in self._analyse_result if result.channel in selected_channels]

        self.__refresh_result_table__(filtered_results)

    def __update_progress_text__(self):
        self.result_dialog.set_text("Analysing...")

    def __get_blf_path__(self) -> str:
        return self.ui.filePathEdit.text().strip()

    def __get_watching_list__(self) -> List[Tuple[str, SignalData]]:
        """从 tableWatch 中提取所有关注信号"""
        watching_list = []
        table = self.ui.tableWatch
        for row in range(table.rowCount()):
            row_data = []
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append("")
            # 跳过完全空的行
            if any(row_data):
                watching_list.append(self.__from_table_row__(row_data))
        return watching_list

    def __refresh_result_table__(self, showing_list: List[AnalyseResult]):
        # 禁用表格更新，一次性创建需要的条目
        self.ui.tableResult.setUpdatesEnabled(False)
        self.ui.tableResult.setRowCount(len(showing_list))

        for row, analyse_result in enumerate(showing_list):
            # Timestamp
            time_item = QTableWidgetItem(analyse_result.timestamp)
            time_item.setTextAlignment(Qt.AlignCenter)
            self.ui.tableResult.setItem(row, INDEX_RESULT_TIMESTAMP, time_item)
            # Channel
            channel_item = QTableWidgetItem(analyse_result.channel)
            channel_item.setTextAlignment(Qt.AlignCenter)
            self.ui.tableResult.setItem(row, INDEX_RESULT_CHANNEL, channel_item)
            # Direction
            direction_item = QTableWidgetItem(analyse_result.direction)
            direction_item.setTextAlignment(Qt.AlignCenter)
            self.ui.tableResult.setItem(row, INDEX_RESULT_DIRECTION, direction_item)
            # SignalName
            name_item = QTableWidgetItem(analyse_result.signal_name)
            name_item.setTextAlignment(Qt.AlignCenter)
            self.ui.tableResult.setItem(row, INDEX_RESULT_SIGNAL_NAME, name_item)
            # RawValue
            raw_item = QTableWidgetItem(analyse_result.raw_display)
            raw_item.setTextAlignment(Qt.AlignCenter)
            self.ui.tableResult.setItem(row, INDEX_RESULT_RAW_VALUE, raw_item)
            # PhysicalValue
            physical_item = QTableWidgetItem(analyse_result.physical_display)
            physical_item.setTextAlignment(Qt.AlignCenter)
            self.ui.tableResult.setItem(row, INDEX_RESULT_PHYSICAL_VALUE, physical_item)

        # 刷新表格，恢复更新
        self.ui.tableResult.setUpdatesEnabled(True)
        self.ui.tableResult.viewport().update()

    def __from_table_row__(self, row_data: list) -> (str, SignalData):
        """
        从表格一行数据（字符串列表）创建实例。
        row_data 顺序与成员变量定义一致：
        [can_id, message_name, start_bit, bit_length, factor, offset]
        """
        can_id_str = row_data[INDEX_WATCHING_CAN_ID].strip()
        direction_str = row_data[INDEX_WATCHING_DIRECTION].strip()
        # 支持十六进制（如 "0x123"）或十进制
        if can_id_str.lower().startswith("0x"):
            can_id = int(can_id_str, 16)
        else:
            can_id = int(can_id_str, 0)  # 自动识别 0x 或十进制

        signal_data = SignalData(can_id, row_data[INDEX_WATCHING_SIGNAL_NAME].strip(),
                                 int(row_data[INDEX_WATCHING_START_BIT]), int(row_data[INDEX_WATCHING_BIT_LENGTH]),
                                 float(row_data[INDEX_WATCHING_FACTOR]), float(row_data[INDEX_WATCHING_OFFSET]))
        return direction_str, signal_data

    def __get_selected_channels__(self) -> []:
        selected_channels = []
        for channel, checkbox in self.channel_checkboxes:
            if checkbox.isChecked():
                selected_channels.append(channel)
        return selected_channels

    def __update_channel_filter_options__(self, results: List[AnalyseResult]):
        # 清空旧的通道复选框
        while self.ui.channelFilterLayout.count():
            item = self.ui.channelFilterLayout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.channel_checkboxes.clear()

        # 获取所有唯一通道
        channels = sorted({result.channel for result in results})

        # 为每个通道创建复选框，默认勾选
        for channel in channels:
            checkbox = QCheckBox(f"Channel-{channel}")
            checkbox.setChecked(True)
            checkbox.setStyleSheet("margin-left: 16px;")
            checkbox.stateChanged.connect(self.on_channel_filter_changed)
            self.ui.channelFilterLayout.addWidget(checkbox)
            self.channel_checkboxes.append((channel, checkbox))
