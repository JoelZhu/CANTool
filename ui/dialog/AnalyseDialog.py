from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton


class AnalyseDialog(QDialog):
    blf_path: str

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Analyse Progress")
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)

        main_layout = QVBoxLayout(self)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.label)

        self.close_btn = QPushButton("Close")
        self.close_btn.setVisible(False)
        self.close_btn.clicked.connect(self.accept)

        main_layout.addWidget(self.close_btn)

        self.resize(350, 150)

    def prepare_blf_path(self, blf_path: str):
        self.blf_path = blf_path

    def set_text(self, text: str, is_finished: bool = False, is_error: bool = False):
        self.label.setText(text)
        if is_error:
            self.close_btn.setVisible(True)
        elif is_finished:
            self.close_btn.setVisible(True)
        else:
            self.close_btn.setVisible(False)
