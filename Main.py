import sys

from PyQt5.QtWidgets import QApplication

from core.Util import resource_path
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


if __name__ == "__main__":
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
