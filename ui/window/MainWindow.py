import os

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QGuiApplication
from PyQt5.QtWidgets import QMainWindow

from core.Util import resource_path
from core.base.BaseParser import BaseParser
from ui.page.Home import Ui_MainWindow
from ui.window.AnalyserWindow import AnalyserWindow
from ui.window.CodecWindow import CodecWindow
from ui.window.ConverterWindow import ConverterWindow
from ui.window.MatrixWindow import MatrixWindow
from ui.window.SettingsWindow import SettingsWindow
from ui.window.SubWindow import SubWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 添加图标
        icon_path = resource_path('app_icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 设置主界面类
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
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

    def on_tab_changed(self, index: int):
        sub_window: SubWindow = self.ui.tabWidget.widget(index)
        sub_window.on_window_changed()
