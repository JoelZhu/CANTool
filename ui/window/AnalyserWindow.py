from typing import List

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QSize, QCoreApplication, QModelIndex, QTimer
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QFileDialog, QHeaderView, QTableWidgetItem, QPushButton, QStyle, QWidget, QVBoxLayout, \
    QLabel, QTableWidget, QMessageBox, QCheckBox, QCompleter

from core.AnalyseHelper import AnalyseHelper, AnalyseResult
from core.Util import print_error, print_debug
from core.entity.SignalData import SignalData
from core.format.Format import Format
from core.parser.DBCParser import DBCParser
from ui.dialog.AnalyseDialog import AnalyseDialog
from ui.page.Analyser import Ui_AnalyserWidget
from ui.page.Home import Ui_MainWindow
from ui.window.SubWindow import SubWindow

INDEX_WATCHING_CAN_ID = 0
INDEX_WATCHING_FORMAT = 1
INDEX_WATCHING_DIRECTION = 2
INDEX_WATCHING_SIGNAL_NAME = 3
INDEX_WATCHING_START_BIT = 4
INDEX_WATCHING_BIT_LENGTH = 5
INDEX_WATCHING_FACTOR = 6
INDEX_WATCHING_OFFSET = 7
INDEX_WATCHING_REMOVE = 8
INDEX_WATCHING_SUM = INDEX_WATCHING_REMOVE + 1

WATCHING_COLUMN_RATIOS = {
    INDEX_WATCHING_CAN_ID: 1,
    INDEX_WATCHING_FORMAT: 1,
    INDEX_WATCHING_DIRECTION: 1,
    INDEX_WATCHING_SIGNAL_NAME: 4,
    INDEX_WATCHING_START_BIT: 1,
    INDEX_WATCHING_BIT_LENGTH: 1,
    INDEX_WATCHING_FACTOR: 1,
    INDEX_WATCHING_OFFSET: 1,
    INDEX_WATCHING_REMOVE: 1,
}

INDEX_RESULT_TIMESTAMP = 0
INDEX_RESULT_CHANNEL = 1
INDEX_RESULT_DIRECTION = 2
INDEX_RESULT_SIGNAL_NAME = 3
INDEX_RESULT_RAW_VALUE = 4
INDEX_RESULT_PHYSICAL_VALUE = 5
INDEX_RESULT_SUM = INDEX_RESULT_PHYSICAL_VALUE + 1

RESULT_COLUMN_RATIOS = {
    INDEX_RESULT_TIMESTAMP: 8,
    INDEX_RESULT_CHANNEL: 2,
    INDEX_RESULT_DIRECTION: 2,
    INDEX_RESULT_SIGNAL_NAME: 9,
    INDEX_RESULT_RAW_VALUE: 3,
    INDEX_RESULT_PHYSICAL_VALUE: 6,
}

KEY_FOR_REMOVE_BUTTON = "SignalName"


class AnalyserWindow(SubWindow):
    def __init__(self, main_ui: Ui_MainWindow):
        super().__init__(main_ui)

        self.helper = AnalyseHelper()

        self.result_dialog = None
        self.channel_checkboxes = []
        self.suggested_list = []

        self._watching_map = {}  # can_id -> list[str, SignalData]
        self._analyse_result: List[AnalyseResult] = list()

        # 设置 ui 类
        self.ui = Ui_AnalyserWidget()
        self.ui.setupUi(self)
        self.setup_table()

        self.suggested_model = QStandardItemModel()
        self.completer = QCompleter(self.suggested_list)
        self.setup_suggestion()
        DBCParser.register_dbc_change_callback(self.__refresh_suggestions)

        self.ui.addButton.clicked.connect(self.on_add_signal)
        self.ui.browseButton.clicked.connect(self.on_browse_clicked)
        self.ui.analyseButton.clicked.connect(self.on_analyse)
        self.ui.analyseButton.setEnabled(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 窗口大小改变时重新应用列宽
        QTimer.singleShot(200, self.__apply_tables_column_ratios__)

    def closeEvent(self, event):
        self.helper.on_close_event()
        event.accept()

    def mark_as_required(self) -> List[QLabel]:
        return [self.main_ui.labelFormat, self.main_ui.labelCanId, self.main_ui.labelStartBit,
                self.main_ui.labelBitLength, self.main_ui.labelFactor, self.main_ui.labelOffset]

    def setup_table(self):
        # 信号关注表
        # 设置行高、不显示行标题
        self.ui.tableWatch.verticalHeader().setDefaultSectionSize(32)
        self.ui.tableWatch.verticalHeader().setVisible(False)
        # 始终显示滚动条
        self.ui.tableWatch.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # 固定宽度列
        # 禁止用户手动调整列宽
        header = self.ui.tableWatch.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        # 禁止表格编辑
        self.ui.tableWatch.setEditTriggers(QTableWidget.NoEditTriggers)

        # 设置行高、不显示行标题
        self.ui.tableResult.verticalHeader().setDefaultSectionSize(32)
        self.ui.tableResult.verticalHeader().setVisible(False)
        # 始终显示滚动条
        self.ui.tableResult.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # 禁止用户手动调整列宽
        header = self.ui.tableResult.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        # 禁止表格编辑
        self.ui.tableResult.setEditTriggers(QTableWidget.NoEditTriggers)

        # 延迟应用一次初始列宽
        QTimer.singleShot(0, self.__apply_tables_column_ratios__)

    def setup_suggestion(self):
        self.completer.setModel(self.suggested_model)
        self.completer.setCompletionRole(Qt.DisplayRole)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)  # 不区分大小写
        self.completer.setFilterMode(Qt.MatchContains)  # 包含匹配（默认是 MatchStartsWith）
        self.completer.setCompletionMode(QCompleter.PopupCompletion)  # 弹出下拉列表
        self.completer.activated[QModelIndex].connect(self.on_suggestion_activated)
        self.ui.editSignalName.setCompleter(self.completer)  # 关联到输入框
        self.__refresh_suggestions()

    def on_add_signal(self):
        try:
            self.__add_signal_inner__()
            self.__update_analyse_enable__()
        except Exception as e:
            QMessageBox.critical(self, "Add signal got exception.", str(e))

    def on_suggestion_activated(self, index: QModelIndex):
        # 获取完整数据对象
        signal_data = index.data(Qt.UserRole)
        if signal_data is None:
            return
        print_debug(f"Selected signal: {signal_data.signal_name} in suggestion.")
        # 延迟执行，防止信号名输入框被自动填充覆盖
        QTimer.singleShot(0, lambda: self.__update_signal_to_edits__(signal_data))

    def on_browse_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select a BLF file", "", "BLF Files (*.blf);;All Files (*)"
        )
        if file_path:
            self.ui.filePathEdit.setText(file_path)
            self.__update_analyse_enable__()

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
        self.helper.start_analysing(blf_path, self._watching_map)

    def on_channel_filter_changed(self, state):
        self.__apply_channel_filter__()

    def on_start(self):
        self.__update_progress_text__()

        watching_list = self.__get_watching_list__()
        self._watching_map.clear()
        for signal in watching_list:
            self._watching_map.setdefault(signal.can_id, []).append((signal.direction, signal))

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

    def __apply_tables_column_ratios__(self):
        self.__apply_watching_column_ratios__()
        self.__apply_result_column_ratios__()

    def __apply_watching_column_ratios__(self):
        self.__apply_table_column_ratios__(self.ui.tableWatch, WATCHING_COLUMN_RATIOS)

    def __apply_result_column_ratios__(self):
        self.__apply_table_column_ratios__(self.ui.tableResult, RESULT_COLUMN_RATIOS)

    def __apply_table_column_ratios__(self, table: QtWidgets.QTableWidget, column_ratio):
        viewport_width = table.viewport().width()
        # 如果宽度无效（例如表格还未显示），直接返回
        if viewport_width <= 0:
            return

        total_ratio = sum(column_ratio.values())
        # 先计算每列的理论宽度（浮点数）
        widths_float = {column: viewport_width * ratio / total_ratio for column, ratio in column_ratio.items()}

        # 向下取整，并计算剩余像素
        widths_int = {column: int(width) for column, width in widths_float.items()}
        remainder = viewport_width - sum(widths_int.values())

        # 将剩余像素按比例分配给前几列
        # 这里按顺序给前 remainder 列各加 1 像素
        columns = list(column_ratio.keys())
        for index in range(remainder):
            widths_int[columns[index % len(columns)]] += 1

        # 应用列宽
        for column, width in widths_int.items():
            table.setColumnWidth(column, width)

    def __add_signal_inner__(self):
        # 1.1 获取矩阵信息
        _, signal_data = self.get_and_check_if_parameters_legal()
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
        self.ui.tableWatch.setItem(row, INDEX_WATCHING_FORMAT, QTableWidgetItem(Format.get_short(signal_data.format)))
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
        remove_button.setProperty(KEY_FOR_REMOVE_BUTTON, signal_name)
        remove_button.clicked.connect(lambda checked, button=remove_button: self.__remove_signal_inner__(button))
        remove_container = QWidget()
        vbox = QVBoxLayout(remove_container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(remove_button, alignment=Qt.AlignCenter)
        self.ui.tableWatch.setCellWidget(row, INDEX_WATCHING_REMOVE, remove_container)

        if row == 1:
            # 表格内容第一次添加时，重新应用列宽
            QTimer.singleShot(0, self.__apply_watching_column_ratios__)

    def __remove_signal_inner__(self, button: QPushButton):
        signal_name = button.property(KEY_FOR_REMOVE_BUTTON)
        if not signal_name:
            print_error(f"Illegal signal name to remove.")
            return

        for row in range(self.ui.tableWatch.rowCount()):
            item = self.ui.tableWatch.item(row, INDEX_WATCHING_SIGNAL_NAME)
            if item and item.text() == signal_name:
                self.ui.tableWatch.removeRow(row)
                self.__update_analyse_enable__()
                break

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

    def __get_watching_list__(self) -> List[SignalData]:
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

    def __refresh_suggestions(self):
        self.suggested_model.clear()
        for signal in DBCParser.query_all_loaded_signals():
            suggested_item = QStandardItem(f"0x{hex(signal.can_id)[2:].upper()} - {signal.signal_name}")
            # 将完整数据存入 UserRole（也可存入多个角色）
            suggested_item.setData(signal, Qt.UserRole)
            self.suggested_model.appendRow(suggested_item)

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

        QTimer.singleShot(0, self.__apply_result_column_ratios__)

    def __from_table_row__(self, row_data: list) -> SignalData:
        # 从表格一行数据（字符串列表）创建实例。row_data 顺序与按照 INDEX_XXX 来匹配
        can_id_str = row_data[INDEX_WATCHING_CAN_ID].strip()
        if can_id_str.lower().startswith("0x"):
            can_id = int(can_id_str, 16)  # 支持十六进制（如 "0x123"）或十进制
        else:
            can_id = int(can_id_str, 0)  # 自动识别 0x 或十进制
        fmt = Format.get_format(row_data[INDEX_WATCHING_FORMAT])

        signal_data = SignalData(fmt, can_id, row_data[INDEX_WATCHING_DIRECTION].strip(),
                                 row_data[INDEX_WATCHING_SIGNAL_NAME].strip(), int(row_data[INDEX_WATCHING_START_BIT]),
                                 int(row_data[INDEX_WATCHING_BIT_LENGTH]), float(row_data[INDEX_WATCHING_FACTOR]),
                                 float(row_data[INDEX_WATCHING_OFFSET]))
        return signal_data

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

    def __update_signal_to_edits__(self, signal_data: SignalData):
        self.update_parameters(signal_data)
        self.ui.editSignalName.setText(signal_data.signal_name)

    def __update_analyse_enable__(self):
        watching_row_count = self.ui.tableWatch.rowCount()
        blf_file_path = self.__get_blf_path__()
        if watching_row_count and blf_file_path:
            self.ui.analyseButton.setEnabled(True)
        else:
            self.ui.analyseButton.setEnabled(False)
