#!/usr/bin/python3
"""
Frontend for ITU project - file manager
"""

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


class FileExplorerWidget(QSplitter):

    CMD_IN_MAX_HEIGHT = 25
    CMD_OUT_MAX_HEIGHT = 2 * CMD_IN_MAX_HEIGHT
    CMD_IN_PLACEHOLDER = ""
    FILES_WINDOW_COLUMNS = 3
    FILES_WINDOW_TOP_FRAME_HEIGHT = 30

    def __init__(self, language):
        super(FileExplorerWidget, self).__init__(Qt.Vertical)
        #self.hlayout = QHBoxLayout(self)
        #self.setLayout(self.hlayout)
        self.language = language
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
        self.files.setHorizontalHeaderLabels(MainWindow.NAMES[self.language]["files_header"])
        self.files.verticalHeader().setVisible(False)
        header = self.files.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

        # Left window terminal
        self.cmd_in = QLineEdit(self.files)
        self.cmd_in.setMaximumHeight(FileExplorerWidget.CMD_IN_MAX_HEIGHT)
        self.cmd_in.setPlaceholderText(FileExplorerWidget.CMD_IN_PLACEHOLDER)
        self.cmd_out = QTextEdit(self.files)
        self.cmd_out.setMaximumHeight(FileExplorerWidget.CMD_OUT_MAX_HEIGHT)
        self.cmd_out.setReadOnly(True)

        # Combo box for disk selection
        self.addWidget(self.topf)
        self.addWidget(self.files)
        self.addWidget(self.cmd_out)
        self.addWidget(self.cmd_in)


# TODO: Use QFontDialog to get user to select the font
# TODO: Button to add or remove explorer?
class MainWindow(QMainWindow):

    NAMES = {
        "cz": {
            "title": "ITU Prohlížeč souborů",
            "files_header": ["Název", "Velikost", "Datum úpravy"]
        },
        "en": {
            "title": "ITU File explorer"
        }
    }

    TOP_WINDOW_MAX_HEIGHT = 90
    EXPLORER_AMOUNT = 2

    def __init__(self, width, height, language="cz"):
        super(MainWindow, self).__init__()
        self.language = language
        self.resize(width, height)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(MainWindow.NAMES[self.language]["title"])
        self.center()

        # Making the space above left and right window
        self.top_frame = QFrame(self)
        self.top_frame.setMaximumHeight(MainWindow.TOP_WINDOW_MAX_HEIGHT)

        # Creating explorer windows
        self.explorers = [FileExplorerWidget(self.language) for _ in range(MainWindow.EXPLORER_AMOUNT)]

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

    def center(self):
        """
        Inspired by https://stackoverflow.com/a/20244839
        :return:
        """
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        center = QApplication.desktop().screenGeometry(screen).center()
        self.move(center.x() - self.width()/2, center.y() - self.height()/2)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow(1024, 600)

    sys.exit(app.exec_())