import os
import sys
import traceback
from datetime import datetime

from PyQt5.QtWidgets import QApplication

from core.Util import resource_path, print_debug, print_error
from core.parser.DBCParser import DBCParser
from core.parser.MessageParser import MessageParser
from ui.ThemeUtil import ThemeUtil
from ui.window.MainWindow import MainWindow


def __apply_material_theme__(material_qss_name: str):
    base_qss_path = resource_path(f"ui/material_base.qss")
    with open(base_qss_path, "r", encoding="utf-8") as base_file_reader:
        base_read = base_file_reader.read()
    qss_path = resource_path(f"ui/{material_qss_name}.qss")
    with open(qss_path, "r", encoding="utf-8") as color_file_reader:
        color_read = color_file_reader.read()
        app.setStyleSheet(base_read + color_read)


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
        except Exception as e:
            print_error(f"Failed to write crash log: {e}")

        # 调用默认处理（打印到 stderr）
        sys.__excepthook__(exception_type, exception_value, exception_traceback)

    # 替换全局异常钩子
    sys.excepthook = handle_exception


if __name__ == "__main__":
    __setup_exception_hook__()

    app = QApplication(sys.argv)

    # 应用主题样式
    __apply_material_theme__(ThemeUtil.query_theme())
    ThemeUtil.register_theme_changed(__apply_material_theme__)

    # 初始化解析器
    MessageParser.init_parser()

    # 加载已经加载过的 DBC 文件
    DBCParser.init_parser()

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
