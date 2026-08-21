import sys

from PyQt5.QtWidgets import QApplication

from core.Util import resource_path
from ui.window.MainWindow import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 应用 Material 样式
    qss_path = resource_path('ui/material_style.qss')
    with open(qss_path, "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
