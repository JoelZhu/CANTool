import os
import sys
from datetime import datetime
from enum import Enum

from PyQt5.QtCore import QSettings, QT_TRANSLATE_NOOP, QCoreApplication
from PyQt5.QtWidgets import QFileDialog, QWidget
from colorama import init, Fore, Style

# 为了日志样式的初始化
init()

settings = QSettings("Joel", "CANTool")


class FileType(Enum):
    BLF = QT_TRANSLATE_NOOP("DialogTitle", "Select a BLF file"), "BLF Files (*.blf);;All Files (*)"
    DBC = QT_TRANSLATE_NOOP("DialogTitle", "Select a DBC file"), "DBC Files (*.dbc);;All Files (*)"


def resource_path(relative_path):
    """获取资源文件的绝对路径，兼容开发环境和 PyInstaller 打包后"""
    if hasattr(sys, '_MEIPASS'):
        # 打包后，资源文件被解压到 _MEIPASS 目录
        base_path = sys._MEIPASS
    else:
        # 开发环境，使用当前文件所在目录
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)


def trigger_file_select(widget: QWidget, file_type: FileType) -> str:
    title = QCoreApplication.translate("DialogTitle", file_type.value[0])
    file_path, _ = QFileDialog.getOpenFileName(widget, title, "", file_type.value[1])
    return file_path


def print_debug(content: str):
    print(Fore.WHITE + f"{datetime.now()}: D {content}" + Style.RESET_ALL)


def print_warn(content: str):
    print(Fore.YELLOW + f"{datetime.now()}: W {content}" + Style.RESET_ALL)


def print_error(content: str):
    print(Fore.RED + f"{datetime.now()}: E {content}" + Style.RESET_ALL)
