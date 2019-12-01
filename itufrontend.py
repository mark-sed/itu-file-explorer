#!/usr/bin/python3
"""
Frontend for ITU project - file manager
"""

import itubackend
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QMainWindow, QApplication, QDesktopWidget,
                             QSplitter, QFrame, QHBoxLayout, QPushButton,
                             QTextEdit, QWidget, QVBoxLayout, QSizePolicy,
                             QLineEdit, QLabel, QFontDialog, QTableWidget,
                             QTableWidgetItem, QComboBox, QAction,
                             QFormLayout, QGroupBox, QAbstractItemView,
                             QSpinBox, QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
from PyQt5.QtGui import QIcon, QStandardItemModel
import sys
from datetime import datetime

class ExplorerModel(QtGui.QStandardItemModel):

    MIME_FORMAT = "application/x-qabstractitemmodeldatalist"

    def __init__(self, parent):
        super(ExplorerModel, self).__init__()
        self.parent = parent

    # Inspired by http://apocalyptech.com/linux/qt/qtableview/
    def dropMimeData(self, data, action, row, col, parent):
        """
        Drop method
        """
        if data.hasFormat(ExplorerModel.MIME_FORMAT):
            source_item = QtGui.QStandardItemModel()
            source_item.dropMimeData(data, QtCore.Qt.CopyAction, 0, 0, QtCore.QModelIndex())

            item_name = source_item.item(0, 0).text()  # TODO move/copy
            print(self.parent.parent.fm.active.get_name(), item_name)
            #self.parent.move_item(item_name, )

        return super().dropMimeData(data, action, row, 0, parent)

class ExplorerStyle(QtWidgets.QProxyStyle):
    # Inspired by http://apocalyptech.com/linux/qt/qtableview/

    def __init__(self, parent):
        super(ExplorerStyle, self).__init__()
        self.parent = parent

    def drawPrimitive(self, element, option, painter, widget=None):
        """
        Drawing simple effects when moving files
        """
        if element == self.PE_IndicatorItemViewItemDrop and not option.rect.isNull():
            option_new = QtWidgets.QStyleOption(option)
            option_new.rect.setLeft(0)
            if widget:
                option_new.rect.setRight(widget.width())
            option = option_new
        super().drawPrimitive(element, option, painter, widget)


class ExplorerTableView(QtWidgets.QTableView):
    # Inspired by http://apocalyptech.com/linux/qt/qtableview/

    def __init__(self, parent, language):
        super().__init__(parent)
        self.parent = parent
        self.verticalHeader().hide()
        self.language = language
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.horizontalHeader().setSectionsClickable(True)
        self.horizontalHeader().sectionClicked.connect(self.header_clicked)
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.ExtendedSelection)
        self.setShowGrid(False)
        self.setDragDropMode(self.DragDrop)
        self.setDragDropOverwriteMode(False)
        self.setStyle(ExplorerStyle(self))
        self.doubleClicked.connect(self.double_clicked)
        self.clicked.connect(self.was_clicked)
        self.model = ExplorerModel(self)
        self.model.setHorizontalHeaderLabels(MainWindow.NAMES[self.language]["files_header"])
        self.setModel(self.model)

    def update(self, files, dont_hide=False):
        self.model.removeRows(0, self.model.rowCount())
        name = QtGui.QStandardItem("..")
        name.setEditable(False)
        name.setDropEnabled(False)
        name.setDragEnabled(False)
        size = QtGui.QStandardItem("")
        size.setDragEnabled(False)
        changed = QtGui.QStandardItem("")
        changed.setDragEnabled(False)
        self.model.appendRow([name, size, changed])

        for c, i in enumerate(files):
            name = QtGui.QStandardItem(i.get_name())
            name.setEditable(False)
            name.setDropEnabled(False)

            if not i.is_folder():
                size = QtGui.QStandardItem(str(round(i.get_size("KB"), 1)) + " kB")
                changed = QtGui.QStandardItem(datetime.utcfromtimestamp(i.get_modification_time()).strftime('%d/%m/%Y %H:%M:%S'))
            else:
                size = QtGui.QStandardItem("")
                changed = QtGui.QStandardItem("")

            changed.setEditable(False)
            changed.setDropEnabled(False)
            size.setEditable(False)
            size.setDropEnabled(False)

            self.model.appendRow([name, size, changed])

    def header_clicked(self, i):
        if self.parent.sort_by == i:
            self.parent.sort_desc = not self.parent.sort_desc
        else:
            self.parent.sort_by = i
            self.parent.sort_desc = False
        self.parent.update()

    def double_clicked(self, index):
        if index.row() == 0:
            self.parent.fm.set_active(self.parent.fm.active.get_parent())
        else:
            selected = self.parent.displayed[index.row()-1]
            if selected.is_folder():
                self.parent.fm.set_active(selected)
            else:
                selected.open()
        self.parent.update()

    def was_clicked(self, index):
        MainWindow.ACTIVE_EXPLORER = self.parent

    def get_selected(self):
        indexes = self.selectedIndexes()
        selected = []
        for i in range(len(indexes)):
            row = indexes[i].row()-1
            if row == -1:  # Skipping parent folder
                continue
            if row not in selected:
                selected.append(row)
        return [self.parent.displayed[i] for i in selected]


class ComboBox(QtWidgets.QComboBox):
    popupAboutToBeShown = QtCore.pyqtSignal()

    def __init__(self, p, parent):
        super(ComboBox, self).__init__(p)
        self.parent = parent

    def showPopup(self):
        self.popupAboutToBeShown.emit()
        self.parent.update()
        super(ComboBox, self).showPopup()


class FileExplorerWidget(QSplitter):

    CMD_IN_MAX_HEIGHT = 25
    CMD_OUT_MAX_HEIGHT = 2 * CMD_IN_MAX_HEIGHT
    FILES_WINDOW_COLUMNS = 3
    FILES_WINDOW_TOP_FRAME_HEIGHT = 30

    SORT_NAME = 0
    SORT_SIZE = 1
    SORT_CHANGED = 2

    def __init__(self, fm, language):
        super(FileExplorerWidget, self).__init__(Qt.Vertical)
        self.language = language
        self.sort_by = FileExplorerWidget.SORT_NAME
        self.sort_desc = False
        self.fm = fm
        self.reinit()

    def reinit(self):
        # Making the left selection window
        # Frame for disk selection and search
        self.topf = QFrame(self)

        # Set layout
        self.topf_layout = QHBoxLayout(self.topf)
        self.topf.setLayout(self.topf_layout)

        self.topf_layout.setContentsMargins(0, 0, 0, 0)

        self.topf.setMaximumHeight(FileExplorerWidget.FILES_WINDOW_TOP_FRAME_HEIGHT)
        self.topf.setMinimumHeight(FileExplorerWidget.FILES_WINDOW_TOP_FRAME_HEIGHT)
        # Disk selection
        self.disks = ComboBox(self.topf, self)

        # Search field
        self.search = QLineEdit(self.topf)

        self.topf_layout.addWidget(self.disks)
        self.topf_layout.addWidget(self.search)

        self.files = ExplorerTableView(self, self.language)

        # Left window terminal
        self.cmd_in = QLineEdit(self.files)
        self.cmd_in.setMaximumHeight(FileExplorerWidget.CMD_IN_MAX_HEIGHT)
        self.cmd_in.returnPressed.connect(self.cmd_in_entered)
        self.cmd_out = QTextEdit(self.files)
        self.cmd_out.setMaximumHeight(FileExplorerWidget.CMD_OUT_MAX_HEIGHT)
        self.cmd_out.setReadOnly(True)

        # Combo box for disk selection
        self.addWidget(self.topf)
        self.addWidget(self.files)
        self.addWidget(self.cmd_out)
        self.addWidget(self.cmd_in)

        self.update()

    def update(self):
        # Update search field text
        self.search.setPlaceholderText(MainWindow.NAMES[self.language]["search"])
        # Update path in terminal
        self.cmd_in.setPlaceholderText(self.fm.get_prefix())
        # Add disks
        self.disks.clear()
        self.disks.addItems([i.get_name() for i in self.fm.get_disks()])
        # Add files
        self.displayed = self.fm.active.get_content()
        if self.sort_by == FileExplorerWidget.SORT_NAME:
            self.displayed.sort(key=lambda x: x.get_name(), reverse=self.sort_desc)
        elif self.sort_by == FileExplorerWidget.SORT_SIZE:
            self.displayed.sort(key=lambda x: x.get_size() if x.is_file() else 0, reverse=self.sort_desc)
        else:
            self.displayed.sort(key=lambda x: x.get_modification_time() if x.is_file() else 0, reverse=self.sort_desc)
        self.files.update(self.displayed)

    def cmd_in_entered(self):
        formatted_out = "\n"+self.fm.get_prefix()+" "+self.cmd_in.text()+"\n"
        self.cmd_out.setText(self.cmd_out.toPlainText()+formatted_out)
        out, err = itubackend.make_shell_command(self.cmd_in.text(), self.fm.active.get_path())
        if out is not None:
            self.cmd_out.setText(self.cmd_out.toPlainText()+out)
        if err is not None:
            self.cmd_out.setText(self.cmd_out.toPlainText()+err)

        self.cmd_out.moveCursor(QtGui.QTextCursor.End)
        self.cmd_in.setText("")


class MainWindow(QMainWindow):

    NAMES = {
        "cz": {
            "language_name": "Česky",
            "title": "ITU Prohlížeč souborů",
            "files_header": ["Název", "Velikost", "Datum úpravy"],
            "search": "Hledat",
            "new_folder": "Nová složka",
            "new_file": "Nový soubor",
            "action_filter": "Podmíněné vykonání",
            "b_mkdir_mo": "Vytvořit novou složku",
            "b_mkdir_d": "Jméno složky",
            "b_touch_mo": "Vytvořit prázný soubor",
            "b_touch_d": "Jméno souboru",
            "b_delete_mo": "Smazat",
            "b_delete_file_confirm": "Opravdu chcete smazat soubor: ",
            "b_delete_folder_confirm": "Opravdu chcete smazat všechen obsah a složku: ",
            "b_delete_multiple_confirm": "Opravdu chcete smazat všechny tyto položky: ",
            "mb_settings": "Nastavení",
            "mb_set_windows": "Pracovní okna",
            "mb_set_windows_add": "Přidat okno",
            "mb_set_windows_remove": "Odebrat okno",
            "as_windows_amount": "Počet oken",
            "mb_exit": "Ukončit",
            "mb_language": "Jazyk",
            "as_theme": "Motiv",
            "as_theme_light": "Světlý",
            "as_theme_dark": "Tmavý",
            "as_style": "Styl",
            "as_appearance": "Vzhled",
            "as_font": "Písmo",
            "as_apply": "Použít",
            "as_ok": "OK",
            "as_cancel": "Zrušit",
            "as_icon_size": "Velikost tlačítek",
            "as_normal": "Normální",
            "as_bigger": "Vetší",
            "mb_advanced": "Pokročilé nastavení",
            "e_file_exists": "Soubor s tímto jménem již existuje",
            "e_folder_exists": "Složka s tímto jménem již existuje",
            "e_other": "Při operaci nastala chyba",
            "error": "Chyba",
            "close": "Zavřít",
            "yes": "Ano",
            "no": "Ne",
            "warning": "Pozor",
        },
        "en": {
            "language_name": "English",
            "title": "ITU File explorer",
        },
        "fr": {
            "language_name": "Français",
            "title": "Explorateur de Fichiers",
        }
    }

    TOP_WINDOW_MAX_HEIGHT = 40
    EXPLORER_AMOUNT = 2
    MAX_EXPLORER_AMOUNT = 5
    ACTIVE_EXPLORER = None

    def __init__(self, width, height, language="cz"):
        super(MainWindow, self).__init__()
        self.setWindowIcon(QIcon("./icons/logo.svg"))
        self.language = language
        self.resize(width, height)
        # Setting light palette
        self.light_palette = QtGui.QPalette()
        # Setting dark palette
        self.dark_palette = QtGui.QPalette()
        self.dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
        self.dark_palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
        self.dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(15, 15, 15))
        self.dark_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53, 53, 53))
        self.dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
        self.dark_palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
        self.dark_palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
        self.dark_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
        self.dark_palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
        self.dark_palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
        self.dark_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(142, 45, 197).lighter())
        self.dark_palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)

        # Set settings windows
        self.error = QMessageBox()
        self.confirm = QMessageBox()
        self.confirm.setIcon(QMessageBox.Question)
        self.confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        self.fms = [itubackend.FileManager() for _ in range(MainWindow.EXPLORER_AMOUNT)]

        self.bigger_icons = False
        self.theme = MainWindow.NAMES["cz"]["as_theme_light"]
        self.settings_window = SettingsWindow(self)

        # Center the screen
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        center = QApplication.desktop().screenGeometry(screen).center()
        self.move(center.x() - self.width() / 2, center.y() - self.height() / 2)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(MainWindow.NAMES[self.language]["title"])

        # Init error window
        self.error.setIcon(QMessageBox.Critical)
        self.error.setWindowTitle(MainWindow.NAMES[self.language]["error"])
        self.error.setStandardButtons(QMessageBox.Close)
        cancel = self.error.button(QMessageBox.Close)
        cancel.setText(MainWindow.NAMES[self.language]["close"])

        self.confirm.setWindowTitle(MainWindow.NAMES[self.language]["warning"])
        yes = self.confirm.button(QMessageBox.Yes)
        no = self.confirm.button(QMessageBox.No)
        yes.setText(MainWindow.NAMES[self.language]["yes"])
        no.setText(MainWindow.NAMES[self.language]["no"])

        self.main_widget = QWidget(self)

        self.menuBar().clear()
        # Adding menu bar
        self.menu_bar = self.menuBar()

        # Settings menu
        self.mb_settings = self.menu_bar.addMenu(MainWindow.NAMES[self.language]["mb_settings"])

        # Settings - Working windows
        self.mb_set_windows = self.mb_settings.addMenu(MainWindow.NAMES[self.language]["mb_set_windows"])
        self.mb_set_windows_add = QAction(MainWindow.NAMES[self.language]["mb_set_windows_add"])
        self.mb_set_windows_remove = QAction(MainWindow.NAMES[self.language]["mb_set_windows_remove"])
        self.mb_set_windows.addAction(self.mb_set_windows_add)
        self.mb_set_windows.addAction(self.mb_set_windows_remove)
        self.mb_set_windows_add.triggered.connect(self.add_explorer)
        if MainWindow.EXPLORER_AMOUNT >= MainWindow.MAX_EXPLORER_AMOUNT:
            self.mb_set_windows_add.setEnabled(False)
        else:
            self.mb_set_windows_add.setEnabled(True)
        self.mb_set_windows_remove.triggered.connect(self.remove_explorer)
        if MainWindow.EXPLORER_AMOUNT <= 1:
            self.mb_set_windows_remove.setEnabled(False)
        else:
            self.mb_set_windows_remove.setEnabled(True)

        # Settings - Advanced
        self.mb_advanced = QAction(MainWindow.NAMES[self.language]["mb_advanced"])
        self.mb_settings.addAction(self.mb_advanced)
        self.mb_advanced.triggered.connect(lambda: (self.settings_window.update(), self.settings_window.show()))

        # Settings - exit
        self.mb_exit = QAction(MainWindow.NAMES[self.language]["mb_exit"])
        self.mb_settings.addAction(self.mb_exit)
        self.mb_exit.triggered.connect(lambda: app.exit())

        # Language menu
        """
        self.mb_language = self.menu_bar.addMenu(MainWindow.NAMES[self.language]["mb_language"])
        self.mb_lan_cz = QAction(MainWindow.NAMES["cz"]["language_name"])
        self.mb_lan_en = QAction(MainWindow.NAMES["en"]["language_name"])
        self.mb_lan_fr = QAction(MainWindow.NAMES["fr"]["language_name"])
        self.mb_language.addAction(self.mb_lan_cz)
        self.mb_language.addAction(self.mb_lan_en)
        self.mb_language.addAction(self.mb_lan_fr)
        """

        # Making the space above left and right window
        self.top_frame = QFrame(self)
        self.top_frame.setMaximumHeight(MainWindow.TOP_WINDOW_MAX_HEIGHT)

        self.top_frame_layout = QHBoxLayout(self.top_frame)
        self.top_frame_layout.setContentsMargins(0, 5, 0, 0)

        # Buttons - Icons are from https://freeicons.io/
        #self.b_settings = QPushButton(self.top_frame)
        #self.b_settings.setIcon(QIcon('./icons/settings.svg'))

        self.b_mkdir = QPushButton(self.top_frame)
        self.b_mkdir.setIcon(QIcon('./icons/mkdir.svg'))
        self.b_mkdir.setToolTip(MainWindow.NAMES[self.language]["b_mkdir_mo"])
        if self.bigger_icons:
            self.b_mkdir.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.b_mkdir.pressed.connect(self.mkdir)

        self.b_touch = QPushButton(self.top_frame)
        self.b_touch.setIcon(QIcon('./icons/touch.svg'))
        self.b_touch.setToolTip(MainWindow.NAMES[self.language]["b_touch_mo"])
        if self.bigger_icons:
            self.b_touch.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.b_touch.pressed.connect(self.touch)

        self.b_delete = QPushButton(self.top_frame)
        self.b_delete.setIcon(QIcon('./icons/delete.svg'))
        self.b_delete.setToolTip(MainWindow.NAMES[self.language]["b_delete_mo"])
        if self.bigger_icons:
            self.b_delete.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.b_delete.pressed.connect(self.rm)

        self.action_filter = QLineEdit(self.top_frame)
        self.action_filter.setPlaceholderText(MainWindow.NAMES[self.language]["action_filter"])
        self.action_filter.setMinimumWidth(300)

        self.top_button_frame = QFrame(self.top_frame)
        self.top_button_frame_layout = QHBoxLayout(self.top_button_frame)
        self.top_button_frame_layout.setContentsMargins(0, 0, 0, 0)
        self.top_button_frame.setMinimumHeight(30)

        #self.top_button_frame_layout.addWidget(self.b_settings)
        self.top_button_frame_layout.addWidget(self.b_mkdir)
        self.top_button_frame_layout.addWidget(self.b_touch)
        self.top_button_frame_layout.addWidget(self.b_delete)

        self.top_frame_layout.addWidget(self.top_button_frame, alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.top_frame_layout.addWidget(self.action_filter, alignment=QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)

        # Creating explorer windows
        self.explorers = [FileExplorerWidget(self.fms[i], self.language) for i in range(MainWindow.EXPLORER_AMOUNT)]
        #self.explorers = [FileExplorerWidget(itubackend.FileManager("/home/marek"), self.language), FileExplorerWidget(itubackend.FileManager("/home"), self.language)]
        MainWindow.ACTIVE_EXPLORER = self.explorers[0]

        # Adding a splitter
        self.splitter = QSplitter(Qt.Horizontal)

        for i in self.explorers:
            self.splitter.addWidget(i)

        self.setCentralWidget(self.main_widget)

        self.layout = QVBoxLayout(self.main_widget)

        # Add top frame where will the buttons be
        self.layout.addWidget(self.top_frame)
        # Add splitter under
        self.layout.addWidget(self.splitter)

        self.show()

    def add_explorer(self):
        if MainWindow.EXPLORER_AMOUNT < MainWindow.MAX_EXPLORER_AMOUNT:
            MainWindow.EXPLORER_AMOUNT += 1
            self.fms.append(itubackend.FileManager())
            self.initUI()

    def remove_explorer(self):
        if MainWindow.EXPLORER_AMOUNT > 1:
            MainWindow.EXPLORER_AMOUNT -= 1
            self.fms = self.fms[:-1]
            self.initUI()
            MainWindow.ACTIVE_EXPLORER = self.explorers[0]

    def dark_mode(self):
        self.theme = MainWindow.NAMES["cz"]["as_theme_dark"]
        app.setPalette(self.dark_palette)

    def light_mode(self):
        self.theme = MainWindow.NAMES["cz"]["as_theme_light"]
        app.setPalette(self.light_palette)

    def mkdir(self):
        if MainWindow.ACTIVE_EXPLORER is not None:
            name, ok = QInputDialog().getText(self, MainWindow.NAMES[self.language]["b_mkdir_mo"],
                                              MainWindow.NAMES[self.language]["b_mkdir_d"], QLineEdit.Normal,
                                              MainWindow.NAMES[self.language]["new_folder"])
            if ok:
                try:
                    MainWindow.ACTIVE_EXPLORER.fm.active.create_folder(name)
                except FileExistsError as e:
                    self.error.setText(MainWindow.NAMES[self.language]["e_folder_exists"])
                    self.error.exec()
                except Exception:
                    self.error.setText(MainWindow.NAMES[self.language]["e_other"])
                    self.error.exec()
                self.initUI()

    def touch(self):
        if MainWindow.ACTIVE_EXPLORER is not None:
            name, ok = QInputDialog().getText(self, MainWindow.NAMES[self.language]["b_touch_mo"],
                                              MainWindow.NAMES[self.language]["b_touch_d"], QLineEdit.Normal,
                                              MainWindow.NAMES[self.language]["new_file"])
            if ok:
                try:
                    MainWindow.ACTIVE_EXPLORER.fm.active.create_file(name)
                except FileExistsError as e:
                    self.error.setText(MainWindow.NAMES[self.language]["e_file_exists"])
                    self.error.exec()
                except Exception:
                    self.error.setText(MainWindow.NAMES[self.language]["e_other"])
                    self.error.exec()
                self.initUI()

    def rm(self):
        if MainWindow.ACTIVE_EXPLORER is not None:
            selected = MainWindow.ACTIVE_EXPLORER.files.get_selected()
            if len(selected) > 1:
                all = ", ".join([a.get_name() for a in selected])
                self.confirm.setText(MainWindow.NAMES[self.language]["b_delete_multiple_confirm"])
                self.confirm.setInformativeText(all)
            elif selected[0].is_file():
                self.confirm.setText(MainWindow.NAMES[self.language]["b_delete_file_confirm"])
                self.confirm.setInformativeText(selected[0].get_name())
            else:
                self.confirm.setText(MainWindow.NAMES[self.language]["b_delete_folder_confirm"])
                self.confirm.setInformativeText(selected[0].get_name())

            ok = self.confirm.exec()
            if ok == QMessageBox.Yes:
                try:
                    for i in selected:
                        i.remove()
                except FileExistsError:
                    self.error.setText(MainWindow.NAMES[self.language]["e_file_exists"])
                    self.error.exec()
                except Exception:
                    self.error.setText(MainWindow.NAMES[self.language]["e_other"])
                    self.error.exec()
                self.initUI()


class SettingsWindow(QMainWindow):

    MIN_WIDTH = 300
    MAX_WIDTH = 500
    STYLES = [i.lower() for i in QtWidgets.QStyleFactory.keys()]

    def __init__(self, parent=None):
        super(SettingsWindow, self).__init__(parent)
        self.parent = parent
        # Center the screen
        self.setMinimumWidth(SettingsWindow.MIN_WIDTH)
        self.setMaximumWidth(SettingsWindow.MAX_WIDTH)
        self.initUI()
        self.old_explorers = MainWindow.EXPLORER_AMOUNT
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        center = QApplication.desktop().screenGeometry(screen).center()
        self.move(center.x() - self.width() / 2, center.y() - self.height() / 2)
        self.update()

    def initUI(self):
        self.setWindowTitle(MainWindow.NAMES[self.parent.language]["mb_advanced"])
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)

        # Appearance
        self.group_design = QGroupBox(MainWindow.NAMES[self.parent.language]["as_appearance"])
        self.layout_form = QFormLayout()
        self.themes = QComboBox()
        self.themes.addItems([MainWindow.NAMES[self.parent.language]["as_theme_light"],
                              MainWindow.NAMES[self.parent.language]["as_theme_dark"]])
        self.themes.currentIndexChanged.connect(self.theme_changed)
        self.layout_form.addRow(QLabel(MainWindow.NAMES[self.parent.language]["as_theme"]),
                                self.themes)
        self.styles = QComboBox()
        self.styles.addItems(SettingsWindow.STYLES)
        self.layout_form.addRow(QLabel(MainWindow.NAMES[self.parent.language]["as_style"]),
                                self.styles)
        self.styles.currentIndexChanged.connect(self.style_changed)

        self.icon_size = QComboBox()
        self.icon_size.addItems([MainWindow.NAMES[self.parent.language]["as_normal"],
                                 MainWindow.NAMES[self.parent.language]["as_bigger"]])
        self.layout_form.addRow(QLabel(MainWindow.NAMES[self.parent.language]["as_icon_size"]),
                                self.icon_size)
        self.icon_size.currentIndexChanged.connect(self.icon_size_changed)

        self.pick_font = QPushButton("Font")
        self.pick_font.clicked.connect(self.picking_font)

        self.layout_form.addRow(QLabel(MainWindow.NAMES[self.parent.language]["as_font"]),
                                self.pick_font)

        self.group_design.setLayout(self.layout_form)
        self.layout.addWidget(self.group_design)

        # Languages
        self.group_languages = QGroupBox(MainWindow.NAMES[self.parent.language]["mb_language"])
        self.languages = QComboBox()
        self.layout_form2 = QFormLayout()
        self.languages.addItems([MainWindow.NAMES["cz"]["language_name"], MainWindow.NAMES["en"]["language_name"],
                                 MainWindow.NAMES["fr"]["language_name"]])
        self.languages.currentIndexChanged.connect(self.language_changed)
        self.layout_form2.addRow(QLabel(MainWindow.NAMES[self.parent.language]["mb_language"]),
                                self.languages)

        self.group_languages.setLayout(self.layout_form2)
        self.layout.addWidget(self.group_languages)

        # Explorers
        self.group_explorers = QGroupBox(MainWindow.NAMES[self.parent.language]["mb_set_windows"])
        self.layout_form3 = QFormLayout()
        self.explorers = QSpinBox()
        self.explorers.setMinimum(1)
        self.explorers.setMaximum(MainWindow.MAX_EXPLORER_AMOUNT)
        self.explorers.setValue(MainWindow.EXPLORER_AMOUNT)
        self.explorers.valueChanged.connect(self.explorer_amount_changed)
        self.layout_form3.addRow(QLabel(MainWindow.NAMES[self.parent.language]["as_windows_amount"]),
                                 self.explorers)

        self.group_explorers.setLayout(self.layout_form3)
        self.layout.addWidget(self.group_explorers)

        # Buttons
        self.button_box = QFrame()
        self.button_layout = QHBoxLayout()
        self.button_box.setLayout(self.button_layout)

        self.b_apply = QPushButton(MainWindow.NAMES[self.parent.language]["as_apply"])
        self.b_ok = QPushButton(MainWindow.NAMES[self.parent.language]["as_ok"])
        self.b_cancel = QPushButton(MainWindow.NAMES[self.parent.language]["as_cancel"])

        self.b_cancel.pressed.connect(self.reset_settings)
        self.b_apply.pressed.connect(self.update)
        self.b_ok.pressed.connect(self.hide)

        self.button_layout.addWidget(self.b_ok, alignment=QtCore.Qt.AlignRight)
        self.button_layout.addWidget(self.b_cancel, alignment=QtCore.Qt.AlignRight)
        self.button_layout.addWidget(self.b_apply, alignment=QtCore.Qt.AlignRight)

        self.layout.addWidget(self.button_box, alignment=QtCore.Qt.AlignRight)

    def update(self):
        self.theme = self.parent.theme
        self.old_font = self.font()
        self.old_style = app.style().objectName()
        self.old_language = self.parent.language

        if MainWindow.EXPLORER_AMOUNT < len(self.parent.fms):  # Remove old explorers
            self.parent.fms = self.parent.fms[:-(len(self.parent.fms)-MainWindow.EXPLORER_AMOUNT)]

        self.old_explorers = MainWindow.EXPLORER_AMOUNT
        self.old_bigger_icons = self.parent.bigger_icons

        if self.parent.bigger_icons:
            self.icon_size.setCurrentIndex(1)
        else:
            self.icon_size.setCurrentIndex(0)

        if self.theme == MainWindow.NAMES["cz"]["as_theme_light"]:
            self.themes.setCurrentIndex(0)
        else:
            self.themes.setCurrentIndex(1)

        if self.parent.language == "cz":
            self.languages.setCurrentIndex(0)
        elif self.parent.language == "en":
            self.languages.setCurrentIndex(1)
        elif self.parent.language == "fr":
            self.languages.setCurrentIndex(2)

        i = SettingsWindow.STYLES.index(app.style().objectName())
        self.styles.setCurrentIndex(i)
        self.explorers.setValue(MainWindow.EXPLORER_AMOUNT)

    def reset_settings(self):
        self.setFont(self.old_font)
        self.parent.setFont(self.old_font)
        app.setStyle(self.old_style)
        if self.theme == MainWindow.NAMES["cz"]["as_theme_light"]:
            self.parent.light_mode()
        else:
            self.parent.dark_mode()
        self.parent.language = self.old_language
        if self.old_explorers < MainWindow.EXPLORER_AMOUNT:  # Remove extra FMs
            self.parent.fms = self.parent.fms[:-(MainWindow.EXPLORER_AMOUNT-self.old_explorers)]
        MainWindow.EXPLORER_AMOUNT = self.old_explorers
        self.parent.bigger_icons = self.old_bigger_icons
        self.parent.initUI()
        self.update()

    def icon_size_changed(self, i):
        if i == 0:
            self.parent.bigger_icons = False
        else:
            self.parent.bigger_icons = True
        self.parent.initUI()

    def picking_font(self):
        font, ok = QFontDialog().getFont()
        if ok:
            self.setFont(font)
            self.parent.setFont(font)

    def explorer_amount_changed(self):
        if self.explorers.value() > MainWindow.EXPLORER_AMOUNT and len(self.parent.fms) < self.explorers.value():
            for _ in range(self.explorers.value()-len(self.parent.fms)):
                self.parent.fms.append(itubackend.FileManager())
        MainWindow.EXPLORER_AMOUNT = self.explorers.value()
        self.parent.initUI()

    def theme_changed(self, i):
        if i == 0:
            self.parent.light_mode()
        else:
            self.parent.dark_mode()

    def language_changed(self, i):
        if i == 0:
            self.parent.language = "cz"
        elif i == 1:
            self.parent.language = "en"
        else:
            self.parent.language = "fr"
        self.parent.initUI()

    def style_changed(self, i):
        app.setStyle(SettingsWindow.STYLES[i])

    def closeEvent(self, event):
        self.reset_settings()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    win = MainWindow(1024, 600)

    sys.exit(app.exec_())
