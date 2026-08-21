import os
import sys
from datetime import datetime

from colorama import init, Fore, Style
# 为了日志样式的初始化
init()


def resource_path(relative_path):
    """获取资源文件的绝对路径，兼容开发环境和 PyInstaller 打包后"""
    if hasattr(sys, '_MEIPASS'):
        # 打包后，资源文件被解压到 _MEIPASS 目录
        base_path = sys._MEIPASS
    else:
        # 开发环境，使用当前文件所在目录
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)


def print_debug(content: str):
    print(Fore.WHITE + f"{datetime.now()}: D {content}" + Style.RESET_ALL)


def print_warn(content: str):
    print(Fore.YELLOW + f"{datetime.now()}: W {content}" + Style.RESET_ALL)


def print_error(content: str):
    print(Fore.RED + f"{datetime.now()}: E {content}" + Style.RESET_ALL)
