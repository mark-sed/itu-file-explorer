#!/usr/bin/python3
"""
Frontend for ITU project - file manager
"""

import itubackend
import PyQt5
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QMainWindow, QApplication, QDesktopWidget,
                             QSplitter, QFrame, QHBoxLayout, QPushButton,
                             QTextEdit, QWidget, QVBoxLayout, QSizePolicy,
                             QLineEdit, QLabel, QFontDialog, QTableWidget,
                             QTableWidgetItem, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
import sys
from datetime import datetime


class FileExplorerWidget(QSplitter):

    CMD_IN_MAX_HEIGHT = 25
    CMD_OUT_MAX_HEIGHT = 2 * CMD_IN_MAX_HEIGHT
    FILES_WINDOW_COLUMNS = 3
    FILES_WINDOW_TOP_FRAME_HEIGHT = 30

    def __init__(self, fm, language):
        super(FileExplorerWidget, self).__init__(Qt.Vertical)
        #self.hlayout = QHBoxLayout(self)
        #self.setLayout(self.hlayout)
        self.language = language
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
        self.disks = QComboBox(self.topf)

        # Search field
        self.search = QLineEdit(self.topf)

        self.topf_layout.addWidget(self.disks)
        self.topf_layout.addWidget(self.search)

        self.files = QTableWidget(self)

        # Adding table to left window
        self.files.setRowCount(0)
        self.files.setColumnCount(FileExplorerWidget.FILES_WINDOW_COLUMNS)
        self.files.verticalHeader().setVisible(False)
        header = self.files.horizontalHeader()
        #header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        #header.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)
        header.setStretchLastSection(True)
        header.resizeSection(0, 250)

        # Left window terminal
        self.cmd_in = QLineEdit(self.files)
        self.cmd_in.setMaximumHeight(FileExplorerWidget.CMD_IN_MAX_HEIGHT)
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
        # Update header labels
        self.files.setHorizontalHeaderLabels(MainWindow.NAMES[self.language]["files_header"])
        # Update path in terminal
        self.cmd_in.setPlaceholderText(self.fm.get_prefix())
        # Add disks
        self.disks.addItems([i.get_name() for i in self.fm.get_disks()])
        # Add files
        self.displayed = self.fm.active.get_content()
        self.files.setRowCount(len(self.displayed))
        # Sort currfiles
        self.displayed.sort(key=lambda x: x.get_name())
        for c, i in enumerate(self.displayed):
            self.files.setItem(c, 0, QTableWidgetItem(i.get_name()))
            # If file then add additional information
            if not i.is_folder():
                # Size
                self.files.setItem(c, 1, QTableWidgetItem(str(round(i.get_size("KB"), 1))+" kB"))
                # Align size to center
                self.files.item(c, 1).setTextAlignment(Qt.AlignCenter)
                # Modification date
                self.files.setItem(c, 2, QTableWidgetItem(datetime.utcfromtimestamp(i.get_modification_time()).
                                                          strftime('%d/%m/%Y %H:%M:%S')))
            else:
                # In case of folder leave the info blank
                self.files.setItem(c, 1, QTableWidgetItem(""))
                self.files.setItem(c, 2, QTableWidgetItem(""))
            # Set cells not editable
            self.files.item(c, 0).setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.files.item(c, 1).setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.files.item(c, 2).setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)


# TODO: Use QFontDialog to get user to select the font
# TODO: Button to add or remove explorer?
class MainWindow(QMainWindow):

    NAMES = {
        "cz": {
            "title": "ITU Prohlížeč souborů",
            "files_header": ["Název", "Velikost", "Datum úpravy"],
            "search": "Hledat",
        },
        "en": {
            "title": "ITU File explorer"
        },
        "fr": {
            "title": "Explorateur de Fichiers"
        }
    }

    TOP_WINDOW_MAX_HEIGHT = 90
    EXPLORER_AMOUNT = 2

    def __init__(self, width, height, language="cz"):
        super(MainWindow, self).__init__()
        self.language = language
        self.resize(width, height)
        # Center the screen
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        center = QApplication.desktop().screenGeometry(screen).center()
        self.move(center.x() - self.width() / 2, center.y() - self.height() / 2)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(MainWindow.NAMES[self.language]["title"])

        # Making the space above left and right window
        self.top_frame = QFrame(self)
        self.top_frame.setMaximumHeight(MainWindow.TOP_WINDOW_MAX_HEIGHT)

        # Creating explorer windows
        self.explorers = [FileExplorerWidget(itubackend.FileManager(), self.language) for _ in range(MainWindow.EXPLORER_AMOUNT)]

        # Adding a splitter
        self.splitter = QSplitter(Qt.Horizontal)

        for i in self.explorers:
            self.splitter.addWidget(i)

        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

        self.layout = QVBoxLayout(self.main_widget)

        # Add top frame where will the buttons be
        self.layout.addWidget(self.top_frame)
        # Add splitter under
        self.layout.addWidget(self.splitter)

        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow(1024, 600)

    sys.exit(app.exec_())