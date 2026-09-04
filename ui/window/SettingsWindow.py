from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QFileDialog, QTableWidget, QHeaderView, QTableWidgetItem, QStyle, QPushButton, QWidget, \
    QVBoxLayout

from core.Util import print_error
from core.parser.DBCParser import DBCParser
from ui.ThemeUtil import ThemeUtil
from ui.page.Home import Ui_MainWindow
from ui.page.Settings import Ui_SettingsWidget
from ui.window.SubWindow import SubWindow

INDEX_DBC_FILE = 0
INDEX_REMOVE = 1
INDEX_SUM = INDEX_REMOVE + 1

KEY_FOR_REMOVE_BUTTON = "DBCPath"


class SettingsWindow(SubWindow):
    def __init__(self, main_ui: Ui_MainWindow):
        super().__init__(main_ui)

        # 设置 ui 类
        self.ui = Ui_SettingsWidget()
        self.ui.setupUi(self)

        self.setup_table()
        self.ui.toggleTheme.toggled.connect(self.on_theme_switched)
        self.ui.toggleTheme.setChecked(ThemeUtil.is_dark_theme())
        self.ui.toggleLSBFirst.toggled.connect(self.on_lsb_first_switched)
        self.ui.toggleLSBFirst.setChecked(DBCParser.get_is_lsb_first())
        self.ui.buttonDBCBrowse.clicked.connect(self.on_browse_clicked)
        self.ui.buttonDBCLoad.clicked.connect(self.on_load_clicked)
        self.ui.buttonDBCLoad.setEnabled(False)

    def setup_table(self):
        self.ui.tableLoadedDBC.setColumnWidth(INDEX_REMOVE, 80)  # RemoveButton
        # 让 DBC File 拉伸，其余列固定
        header = self.ui.tableLoadedDBC.horizontalHeader()
        for col in range(INDEX_SUM):
            if col == INDEX_DBC_FILE:
                header.setSectionResizeMode(col, QHeaderView.Stretch)
            else:
                header.setSectionResizeMode(col, QHeaderView.Fixed)
        # 禁止表格编辑
        self.ui.tableLoadedDBC.setEditTriggers(QTableWidget.NoEditTriggers)
        # 设置表格固定高度
        header_height = self.ui.tableLoadedDBC.horizontalHeader().height()
        rows_height = 3 * self.ui.tableLoadedDBC.verticalHeader().defaultSectionSize()
        self.ui.tableLoadedDBC.setMinimumHeight(header_height + rows_height)
        self.ui.tableLoadedDBC.setMaximumHeight(header_height + rows_height)
        # 不显示列标题
        self.ui.tableLoadedDBC.verticalHeader().setVisible(False)
        # 始终显示滚动条
        self.ui.tableLoadedDBC.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # 加载数据
        self.__refresh_loaded_table__()

    def on_theme_switched(self, is_checked: bool):
        ThemeUtil.set_dark_theme(is_checked)

    def on_lsb_first_switched(self, is_checked: bool):
        DBCParser.switch_lsb_first(is_checked)

    def on_browse_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select a DBC file", "", "DBC Files (*.dbc);;All Files (*)"
        )
        if file_path:
            self.ui.editDBCFilePath.setText(file_path)
            self.ui.buttonDBCLoad.setEnabled(True)

    def on_load_clicked(self):
        dbc_file_path = self.ui.editDBCFilePath.text().strip()
        if dbc_file_path:
            DBCParser.load_dbc(dbc_file_path)
            self.__refresh_loaded_table__()

    def __refresh_loaded_table__(self):
        self.ui.tableLoadedDBC.setRowCount(0)

        stored_files = DBCParser.query_stored_dbc_files()
        for dbc_file in stored_files:
            # 2.1 新增一行
            row = self.ui.tableLoadedDBC.rowCount()
            self.ui.tableLoadedDBC.insertRow(row)
            self.ui.tableLoadedDBC.setItem(row, INDEX_DBC_FILE, QTableWidgetItem(dbc_file))
            # 2.3 显示删除按钮
            remove_icon = self.style().standardIcon(QStyle.SP_TrashIcon)

            remove_button = QPushButton()
            remove_button.setObjectName("removeButton")
            remove_button.setIcon(remove_icon)
            remove_button.setIconSize(QSize(16, 16))
            # 单独编写样式，因为全局样式的原因，只设置高和宽不会生效
            remove_button.setStyleSheet("""
                QPushButton#removeButton {
                    min-height: 0px;
                    max-height: 24px;
                    height: 24px;
                    padding: 0px;
                    margin: 0px;
                    border: none;
                }
            """)
            remove_button.setFixedSize(64, 24)
            remove_button.setProperty(KEY_FOR_REMOVE_BUTTON, dbc_file)
            remove_button.clicked.connect(lambda checked, button=remove_button: self.__remove_dbc_loaded__(button))
            remove_container = QWidget()
            vbox = QVBoxLayout(remove_container)
            vbox.setContentsMargins(0, 0, 0, 0)
            vbox.addWidget(remove_button, alignment=Qt.AlignCenter)
            self.ui.tableLoadedDBC.setCellWidget(row, INDEX_REMOVE, remove_container)

    def __remove_dbc_loaded__(self, button: QPushButton):
        dbc_path = button.property(KEY_FOR_REMOVE_BUTTON)
        if not dbc_path:
            print_error(f"Illegal DBC to unload.")
            return

        for row in range(self.ui.tableLoadedDBC.rowCount()):
            item = self.ui.tableLoadedDBC.item(row, INDEX_DBC_FILE)
            if item and item.text() == dbc_path:
                self.ui.tableLoadedDBC.removeRow(row)
                DBCParser.unload_dbc(dbc_path)
                break
