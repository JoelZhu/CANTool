import os

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton


class ConvertDialog(QDialog):
    blf_path: str

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Convert Progress")
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)

        main_layout = QVBoxLayout(self)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.label)

        # 水平布局：用于按钮
        button_layout = QHBoxLayout()
        self.open_btn = QPushButton("Open")
        self.open_btn.setVisible(False)
        self.open_btn.clicked.connect(self.open_folder)
        button_layout.addWidget(self.open_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.setVisible(False)
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        # 将水平布局添加到主布局中
        main_layout.addLayout(button_layout)

        self.resize(350, 150)

    def prepare_blf_path(self, blf_path: str):
        self.blf_path = blf_path

    def set_text(self, text: str, is_finished: bool = False, is_error: bool = False):
        self.label.setText(text)
        if is_error:
            self.open_btn.setVisible(False)
            self.close_btn.setVisible(True)
        elif is_finished:
            self.open_btn.setVisible(True)
            self.close_btn.setVisible(True)
        else:
            self.open_btn.setVisible(False)
            self.close_btn.setVisible(False)

    def open_folder(self):
        if self.blf_path:
            # 打开文件夹
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(self.blf_path)))
