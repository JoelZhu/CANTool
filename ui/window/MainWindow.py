import os

from PyQt5.QtCore import Qt, QSize, QModelIndex, QTimer
from PyQt5.QtGui import QIcon, QGuiApplication, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QMainWindow, QCompleter

from core.Util import resource_path, settings, print_debug
from core.base.BaseParser import BaseParser
from core.entity.SignalData import SignalData
from core.parser.DBCParser import DBCParser
from ui.page.Home import Ui_MainWindow
from ui.window.AnalyserWindow import AnalyserWindow
from ui.window.CodecWindow import CodecWindow
from ui.window.ConverterWindow import ConverterWindow
from ui.window.MatrixWindow import MatrixWindow
from ui.window.SettingsWindow import SettingsWindow
from ui.window.SubWindow import SubWindow

KEY_WINDOW_SIZE = "WindowSize"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.suggested_list = []

        # 添加图标
        icon_path = resource_path('app_icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 设置主界面类
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.suggested_model = QStandardItemModel()
        self.completer = QCompleter(self.suggested_list)
        self.setup_suggestion()
        DBCParser.register_dbc_change_callback(self.__refresh_suggestions)
        self.ui.editSignalName.setCompleter(self.completer)  # 关联到输入框

        stored_size = settings.value(KEY_WINDOW_SIZE, None)
        if stored_size is not None:
            # 用户自行调整过，使用用户缓存的窗口大小
            self.restoreGeometry(stored_size)
        else:
            # 首次，按照默认设定的窗口大小
            screen = QGuiApplication.primaryScreen()
            available_size = screen.availableGeometry()  # 可用区域
            width = available_size.width()
            height = available_size.height()
            min_size = width if width < height else height
            actual_size = int(min_size * 0.8)
            self.resize(QSize(actual_size, actual_size))

        # 设置每格平分
        for col in range(8):
            self.ui.paramsLayout.setColumnStretch(col, 1)

        # 去掉最大化按钮标志
        flags = self.windowFlags()
        flags &= ~Qt.WindowMaximizeButtonHint
        self.setWindowFlags(flags)

        # 动态添加支持的报文格式
        all_formats = BaseParser.get_all_formats()
        self.ui.comboFormat.clear()
        for fmt in all_formats:
            self.ui.comboFormat.addItem(fmt.value, fmt)

        # 创建页面实例
        self.analyser_page = AnalyserWindow(self.ui)
        self.converter_page = ConverterWindow(self.ui)
        self.codec_page = CodecWindow(self.ui)
        self.matrix_page = MatrixWindow(self.ui)
        self.settings_page = SettingsWindow(self.ui)

        # 添加到 TabWidget
        self.ui.tabWidget.addTab(self.analyser_page, "Analyser")
        self.ui.tabWidget.addTab(self.converter_page, "Converter")
        self.ui.tabWidget.addTab(self.codec_page, "Codec")
        self.ui.tabWidget.addTab(self.matrix_page, "Matrix")
        self.ui.tabWidget.addTab(self.settings_page, "Settings")
        self.ui.tabWidget.currentChanged.connect(self.on_tab_changed)
        # 触发首页的切换回调
        self.on_tab_changed(0)

    def closeEvent(self, event):
        # 保存窗口几何信息（位置 + 大小）
        window_size = self.saveGeometry()
        settings.setValue(KEY_WINDOW_SIZE, window_size)
        super().closeEvent(event)

    def setup_suggestion(self):
        self.completer.setModel(self.suggested_model)
        self.completer.setCompletionRole(Qt.DisplayRole)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)  # 不区分大小写
        self.completer.setFilterMode(Qt.MatchContains)  # 包含匹配（默认是 MatchStartsWith）
        self.completer.setCompletionMode(QCompleter.PopupCompletion)  # 弹出下拉列表
        self.completer.activated[QModelIndex].connect(self.on_suggestion_activated)
        self.__refresh_suggestions()

    def on_suggestion_activated(self, index: QModelIndex):
        # 获取完整数据对象
        signal_data = index.data(Qt.UserRole)
        if signal_data is None:
            return
        print_debug(f"Selected signal: {signal_data.signal_name} in suggestion.")
        # 延迟执行，防止信号名输入框被自动填充覆盖
        QTimer.singleShot(0, lambda: self.__update_signal_to_edits__(signal_data))

    def on_tab_changed(self, index: int):
        sub_window: SubWindow = self.ui.tabWidget.widget(index)
        sub_window.on_window_changed()

    def __refresh_suggestions(self):
        self.suggested_model.clear()
        for signal in DBCParser.query_all_loaded_signals():
            suggested_item = QStandardItem(f"0x{hex(signal.can_id)[2:].upper()} - {signal.signal_name}")
            # 将完整数据存入 UserRole（也可存入多个角色）
            suggested_item.setData(signal, Qt.UserRole)
            self.suggested_model.appendRow(suggested_item)

    def __update_signal_to_edits__(self, signal_data: SignalData):
        self.__update_parameters__(signal_data)
        self.ui.editSignalName.setText(signal_data.signal_name)

    def __update_parameters__(self, data: SignalData):
        self.ui.comboFormat.setCurrentText(data.format.value)
        self.ui.editCanId.setText(hex(data.can_id)[2:].upper())
        self.ui.spinStartBit.setValue(data.start_bit)
        self.ui.spinBitLength.setValue(data.bit_length)
        self.ui.spinFactor.setValue(data.factor)
        self.ui.spinOffset.setValue(data.offset)
