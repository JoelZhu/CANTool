import os

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow

from core.MessageParser import MessageParser
from core.Util import resource_path
from core.base.BaseParser import BaseParser
from ui.page.Home import Ui_MainWindow
from ui.window.AnalyserWindow import AnalyserWindow
from ui.window.ConverterWindow import ConverterWindow
from ui.window.GeneratorWindow import GeneratorWindow
from ui.window.MatrixWindow import MatrixWindow
from ui.window.ParserWindow import ParserWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化解析器
        MessageParser.init_parser()

        # 添加图标
        icon_path = resource_path('app_icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 设置主界面类
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # 动态添加支持的报文格式
        parsers_dict = BaseParser.get_all_parsers()
        self.ui.comboFormat.clear()
        for key, value in parsers_dict.items():
            self.ui.comboFormat.addItem(key.value, value)

        # 创建页面实例
        self.analyser_page = AnalyserWindow(self.ui)
        self.converter_page = ConverterWindow(self.ui)
        self.parser_page = ParserWindow(self.ui)
        self.generator_page = GeneratorWindow(self.ui)
        self.matrix_page = MatrixWindow(self.ui)

        # 添加到 TabWidget
        self.ui.tabWidget.addTab(self.analyser_page, "Analyser")
        self.ui.tabWidget.addTab(self.converter_page, "Converter")
        self.ui.tabWidget.addTab(self.parser_page, "Parser")
        self.ui.tabWidget.addTab(self.generator_page, "Generator")
        self.ui.tabWidget.addTab(self.matrix_page, "Matrix")
