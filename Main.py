import os
import sys
import traceback
from datetime import datetime

from PyQt5.QtCore import QTranslator
from PyQt5.QtGui import QFontDatabase, QFont
from PyQt5.QtWidgets import QApplication

from core.Util import resource_path, print_error, print_debug
from core.parser.DBCParser import DBCParser
from core.parser.MessageParser import MessageParser
from ui.util.LanguageUtil import LanguageUtil
from ui.util.ThemeUtil import ThemeUtil
from ui.window.MainWindow import MainWindow

RESOURCES_BASE = "resources"
QSS_DIRECTORY = f"{RESOURCES_BASE}/styles"
QM_DIRECTORY = f"{RESOURCES_BASE}/languages"
FONT_DIRECTORY = f"{RESOURCES_BASE}/fonts"


def __apply_material_theme__(material_qss_name: str):
    with open(resource_path(f"{QSS_DIRECTORY}/material_base.qss"), "r", encoding="utf-8") as base_file_reader:
        base_read = base_file_reader.read()
    with open(resource_path(f"{QSS_DIRECTORY}/{material_qss_name}.qss"), "r", encoding="utf-8") as color_file_reader:
        color_read = color_file_reader.read()
        app.setStyleSheet(base_read + color_read)


def __apply_language__(language_qm_name: str):
    translator = QTranslator()
    translator.load(resource_path(f"{QM_DIRECTORY}/{language_qm_name}.qm"))
    app.installTranslator(translator)
    app._translator = translator


def __apply_font__():
    font_id = QFontDatabase.addApplicationFont(resource_path(f"{FONT_DIRECTORY}/selawk.ttf"))
    if font_id != -1:
        family = QFontDatabase.applicationFontFamilies(font_id)[0]
        app.setFont(QFont(family))
        print_debug(f"Font: '{family}' load successfully.")
    else:
        print_error("Font load failed.")


def __setup_exception_hook__():
    def handle_exception(exception_type, exception_value, exception_traceback):
        # 忽略键盘中断（用户主动退出）
        if issubclass(exception_type, KeyboardInterrupt):
            sys.__excepthook__(exception_type, exception_value, exception_traceback)
            return

        # 生成时间戳和文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 获取可执行文件所在目录
        if getattr(sys, 'frozen', False):  # 打包成 exe 时
            base_dir = os.path.dirname(sys.executable)
        else:  # 开发环境（脚本运行）
            base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        log_file = os.path.join(base_dir, f"crash_{timestamp}.log")

        # 构建错误信息
        error_message = "".join(traceback.format_exception(exception_type, exception_value, exception_traceback))
        log_content = f"Crash Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        log_content += f"Exception Type: {exception_type.__name__}\n"
        log_content += f"Exception Value: {exception_value}\n"
        log_content += "Traceback:\n"
        log_content += error_message

        # 写入文件
        try:
            with open(log_file, 'w', encoding='utf-8') as file_writer:
                file_writer.write(log_content)
        except Exception as exception:
            print_error(f"Failed to write crash log: {exception}")

        # 调用默认处理（打印到 stderr）
        sys.__excepthook__(exception_type, exception_value, exception_traceback)

    # 替换全局异常钩子
    sys.excepthook = handle_exception


if __name__ == "__main__":
    __setup_exception_hook__()
    app = QApplication(sys.argv)

    __apply_font__()

    # 应用主题样式
    __apply_material_theme__(ThemeUtil.query_theme())
    ThemeUtil.register_theme_changed(__apply_material_theme__)

    # 语言
    __apply_language__(LanguageUtil.get_language().value)
    LanguageUtil.register_language_changed(__apply_language__)

    # 初始化解析器
    MessageParser.init_parser()

    # 加载已经加载过的 DBC 文件
    DBCParser.init_parser()

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
