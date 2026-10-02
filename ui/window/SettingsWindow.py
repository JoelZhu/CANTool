from PyQt5.QtCore import QSize, Qt, QTimer, QRegExp
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QStyle, QPushButton, QWidget, QVBoxLayout, QHeaderView

from core.Util import print_error, trigger_file_select, FileType
from core.parser.DBCParser import DBCParser
from ui.page.Home import Ui_MainWindow
from ui.page.Settings import Ui_SettingsWidget
from ui.util.LanguageUtil import LanguageUtil, Language
from ui.util.ThemeUtil import ThemeUtil
from ui.window.SubWindow import SubWindow, apply_table_column_ratios

INDEX_DBC_FILE = 0
INDEX_ALIAS = 1
INDEX_UNLOAD = 2
INDEX_SUM = INDEX_UNLOAD + 1

COLUMN_RATIOS = {
    INDEX_DBC_FILE: 8,
    INDEX_ALIAS: 2,
    INDEX_UNLOAD: 1,
}

KEY_FOR_UNLOAD_BUTTON = "DBCPath"


class SettingsWindow(SubWindow):
    def __init__(self, main_ui: Ui_MainWindow):
        super().__init__(main_ui)

        # 设置 ui 类
        self.ui = Ui_SettingsWidget()
        self.ui.setupUi(self)

        self.setup_table()
        # 加载数据
        self.__refresh_loaded_table__()

        self.ui.toggleTheme.toggled.connect(self.on_theme_switched)
        self.ui.toggleTheme.setChecked(ThemeUtil.is_dark_theme())
        self.ui.toggleLanguage.toggled.connect(self.on_language_switched)
        self.ui.toggleLanguage.setChecked(LanguageUtil.get_language() == Language.CHINESE)
        self.ui.toggleLSBFirst.toggled.connect(self.on_lsb_first_switched)
        self.ui.toggleLSBFirst.setChecked(DBCParser.get_is_lsb_first())

        self.ui.buttonDBCBrowse.clicked.connect(self.on_browse_clicked)
        validator = QRegExpValidator(QRegExp(r"[0-9A-Za-z_-]*"), self.ui.editAlias)
        self.ui.editAlias.setValidator(validator)
        self.ui.buttonDBCLoad.clicked.connect(self.on_load_clicked)
        self.ui.buttonDBCLoad.setEnabled(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 窗口大小改变时重新应用列宽
        QTimer.singleShot(200, self.__apply_tables_column_ratios__)

    def on_language_changed(self):
        self.ui.retranslateUi(self)
        # 设置表标题
        self.__setup_table_header__()

    def setup_table(self):
        self.ui.tableLoadedDBC.setColumnCount(INDEX_SUM)
        # # 设置表格固定高度
        header_height = self.ui.tableLoadedDBC.horizontalHeader().height()
        rows_height = 3 * self.ui.tableLoadedDBC.verticalHeader().defaultSectionSize()
        self.ui.tableLoadedDBC.setMinimumHeight(header_height + rows_height)
        self.ui.tableLoadedDBC.setMaximumHeight(header_height + rows_height)
        # 不显示列标题
        self.ui.tableLoadedDBC.verticalHeader().setDefaultSectionSize(32)
        self.ui.tableLoadedDBC.verticalHeader().setVisible(False)
        # 始终显示滚动条
        self.ui.tableLoadedDBC.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # 配置列标题属性
        header = self.ui.tableLoadedDBC.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        header.setStretchLastSection(False)
        header.setFixedHeight(28)
        # 禁止表格编辑
        self.ui.tableLoadedDBC.setEditTriggers(QTableWidget.NoEditTriggers)

        # 设置表标题
        self.__setup_table_header__()

        # 延迟应用一次初始列宽
        QTimer.singleShot(0, self.__apply_tables_column_ratios__)

    def on_theme_switched(self, is_checked: bool):
        ThemeUtil.set_dark_theme(is_checked)

    def on_language_switched(self, is_checked: bool):
        LanguageUtil.store_language(Language.CHINESE if is_checked else Language.ENGLISH)

    def on_lsb_first_switched(self, is_checked: bool):
        DBCParser.switch_lsb_first(is_checked)

    def on_browse_clicked(self):
        file_path = trigger_file_select(self, FileType.DBC)
        if file_path:
            self.ui.editDBCFilePath.setText(file_path)
            self.ui.buttonDBCLoad.setEnabled(True)

    def on_load_clicked(self):
        dbc_file_path = self.ui.editDBCFilePath.text().strip()
        dbc_file_alias = self.ui.editAlias.text().strip()
        if dbc_file_path:
            DBCParser.load_dbc(dbc_file_path, dbc_file_alias)
            self.__refresh_loaded_table__()

    def __apply_tables_column_ratios__(self):
        apply_table_column_ratios(self.ui.tableLoadedDBC, COLUMN_RATIOS)

    def __setup_table_header__(self):
        # 设置列标题
        self.ui.tableLoadedDBC.setHorizontalHeaderLabels([self.tr("DBC Path"), self.tr("Alias"), self.tr("Unload")])

    def __refresh_loaded_table__(self):
        self.ui.tableLoadedDBC.setRowCount(0)

        stored_files = DBCParser.query_stored_dbc_files()
        for store_file in stored_files:
            # 2.1 新增一行
            row = self.ui.tableLoadedDBC.rowCount()

            # 2.2 填充数据
            self.ui.tableLoadedDBC.insertRow(row)

            dbc_file_item = QTableWidgetItem(store_file.path)
            dbc_file_item.setToolTip(store_file.path)
            self.ui.tableLoadedDBC.setItem(row, INDEX_DBC_FILE, dbc_file_item)
            dbc_alias_item = QTableWidgetItem(store_file.alias)
            self.ui.tableLoadedDBC.setItem(row, INDEX_ALIAS, dbc_alias_item)

            # 2.3 显示删除按钮
            unload_icon = self.style().standardIcon(QStyle.SP_TrashIcon)
            unload_button = QPushButton()
            unload_button.setObjectName("unloadButton")
            unload_button.setIcon(unload_icon)
            unload_button.setIconSize(QSize(16, 16))
            # 单独编写样式，因为全局样式的原因，只设置高和宽不会生效
            unload_button.setStyleSheet("""
                QPushButton#unloadButton {
                    min-height: 0px;
                    max-height: 24px;
                    height: 24px;
                    padding: 0px;
                    margin: 0px;
                    border: none;
                }
            """)
            unload_button.setFixedSize(64, 24)
            unload_button.setProperty(KEY_FOR_UNLOAD_BUTTON, store_file.path)
            unload_button.clicked.connect(lambda checked, button=unload_button: self.__unload_dbc__(button))
            unload_container = QWidget()
            vbox = QVBoxLayout(unload_container)
            vbox.setContentsMargins(0, 0, 0, 0)
            vbox.addWidget(unload_button, alignment=Qt.AlignCenter)
            self.ui.tableLoadedDBC.setCellWidget(row, INDEX_UNLOAD, unload_container)

    def __unload_dbc__(self, button: QPushButton):
        dbc_path = button.property(KEY_FOR_UNLOAD_BUTTON)
        if not dbc_path:
            print_error(f"Illegal DBC to unload.")
            return

        for row in range(self.ui.tableLoadedDBC.rowCount()):
            item = self.ui.tableLoadedDBC.item(row, INDEX_DBC_FILE)
            if item and item.text() == dbc_path:
                self.ui.tableLoadedDBC.removeRow(row)
                DBCParser.unload_dbc(dbc_path)
                break
