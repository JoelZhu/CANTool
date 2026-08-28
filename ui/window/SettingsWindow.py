from ui.ThemeUtil import ThemeUtil
from ui.page.Home import Ui_MainWindow
from ui.page.Settings import Ui_SettingsWidget
from ui.window.SubWindow import SubWindow


class SettingsWindow(SubWindow):
    def __init__(self, main_ui: Ui_MainWindow):
        super().__init__(main_ui)

        # 设置 ui 类
        self.ui = Ui_SettingsWidget()
        self.ui.setupUi(self)

        self.ui.toggleTheme.toggled.connect(self.on_theme_switched)
        self.ui.toggleTheme.setChecked(ThemeUtil.is_dark_theme())

    def on_theme_switched(self, is_checked: bool):
        ThemeUtil.set_dark_theme(is_checked)
