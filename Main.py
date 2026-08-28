import sys

from PyQt5.QtWidgets import QApplication

from core.Util import resource_path
from ui.ThemeUtil import ThemeUtil
from ui.window.MainWindow import MainWindow


def __apply_material_theme__(material_qss_name: str):
    qss_path = resource_path(f"ui/{material_qss_name}.qss")
    with open(qss_path, "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 应用主题样式
    __apply_material_theme__(ThemeUtil.query_theme())
    ThemeUtil.register_theme_changed(__apply_material_theme__)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
