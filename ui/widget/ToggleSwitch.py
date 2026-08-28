from PyQt5.QtCore import Qt, QRectF, QPropertyAnimation, pyqtProperty, QSize
from PyQt5.QtGui import QPainter, QColor, QBrush
from PyQt5.QtWidgets import QAbstractButton


class ToggleSwitch(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._offset = 0.0  # 0.0 到 1.0，表示滑块位置

        # 默认颜色（可通过 QSS 覆盖）
        self._track_color_on = QColor("#4CAF50")  # 开启时轨道颜色
        self._track_color_off = QColor("#CCCCCC")  # 关闭时轨道颜色
        self._slider_color = QColor("white")  # 滑块颜色

        self.setCheckable(True)
        self.setFixedSize(40, 20)

        self._animation = QPropertyAnimation(self, b"offset", self)
        self._animation.setDuration(120)
        self.toggled.connect(self._animate)

    def _animate(self, checked):
        self._animation.stop()
        self._animation.setStartValue(self._offset)
        self._animation.setEndValue(1.0 if checked else 0.0)
        self._animation.start()

    # ----- offset 属性（用于动画）-----
    def get_offset(self):
        return self._offset

    def set_offset(self, value):
        self._offset = value
        self.update()

    offset = pyqtProperty(float, get_offset, set_offset)

    # ----- 颜色属性 -----
    def get_track_color_on(self):
        return self._track_color_on

    def set_track_color_on(self, color):
        self._track_color_on = QColor(color)
        self.update()

    trackColorOn = pyqtProperty(QColor, get_track_color_on, set_track_color_on)

    def get_track_color_off(self):
        return self._track_color_off

    def set_track_color_off(self, color):
        self._track_color_off = QColor(color)
        self.update()

    trackColorOff = pyqtProperty(QColor, get_track_color_off, set_track_color_off)

    def get_slider_color(self):
        return self._slider_color

    def set_slider_color(self, color):
        self._slider_color = QColor(color)
        self.update()

    sliderColor = pyqtProperty(QColor, get_slider_color, set_slider_color)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 轨道颜色（根据开关状态）
        track_color = self._track_color_on if self.isChecked() else self._track_color_off
        painter.setBrush(QBrush(track_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), self.height() / 2, self.height() / 2)

        # 滑块
        margin = self.height() * 0.1
        slider_diameter = self.height() - 2 * margin
        slider_x = margin + self._offset * (self.width() - self.height())
        painter.setBrush(QBrush(self._slider_color))
        painter.drawEllipse(QRectF(slider_x, margin, slider_diameter, slider_diameter))

    def sizeHint(self):
        return QSize(40, 20)
