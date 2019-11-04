#!/usr/bin/python3
"""
Frontend for ITU project - file manager
"""

import PyQt5
from PyQt5.QtWidgets import (QMainWindow, QApplication, QDesktopWidget,
                             QSplitter, QFrame, QHBoxLayout, QPushButton,
                             QTextEdit, QWidget, QVBoxLayout, QSizePolicy,
                             QLineEdit, QLabel, QFontDialog)
from PyQt5.QtCore import Qt
import sys


# TODO: Use QFontDialog to get user to select the font
class MainWindow(QMainWindow):

    NAMES = {
        "cz": {
            "title": "ITU Prohlížeč souborů",
        },
        "en": {
            "title": "ITU File explorer"
        }
    }

    TOP_WINDOW_MAX_HEIGHT = 90
    CMD_IN_MAX_HEIGHT = 25
    CMD_OUT_MAX_HEIGHT = 2*CMD_IN_MAX_HEIGHT
    CMD_IN_PLACEHOLDER = ""

    def __init__(self, width, height, language="cz"):
        super(MainWindow, self).__init__()
        self.language = language
        self.resize(width, height)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(MainWindow.NAMES[self.language]["title"])
        self.center()

        # Making the left selection window
        self.left_window = QFrame(self)
        self.left_window.setFrameShape(QFrame.StyledPanel)

        # Left window terminal
        self.left_window_cmd_in = QLineEdit(self)
        self.left_window_cmd_in.setMaximumHeight(MainWindow.CMD_IN_MAX_HEIGHT)
        self.left_window_cmd_in.setPlaceholderText(MainWindow.CMD_IN_PLACEHOLDER)
        self.left_window_cmd_out = QTextEdit(self)
        self.left_window_cmd_out.setMaximumHeight(MainWindow.CMD_OUT_MAX_HEIGHT)
        self.left_window_cmd_out.setReadOnly(True)

        self.left_window_splitter = QSplitter(Qt.Vertical)
        self.left_window_splitter.addWidget(self.left_window)
        self.left_window_splitter.addWidget(self.left_window_cmd_out)
        self.left_window_splitter.addWidget(self.left_window_cmd_in)

        # Making the right selection window
        self.right_window = QFrame(self)
        self.right_window.setFrameShape(QFrame.StyledPanel)

        # Left window terminal
        self.right_window_cmd_in = QLineEdit(self)
        self.right_window_cmd_in.setMaximumHeight(MainWindow.CMD_IN_MAX_HEIGHT)
        self.right_window_cmd_in.setPlaceholderText(MainWindow.CMD_IN_PLACEHOLDER)
        self.right_window_cmd_out = QTextEdit(self)
        self.right_window_cmd_out.setMaximumHeight(MainWindow.CMD_OUT_MAX_HEIGHT)
        """
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(self.right_window_cmd_out.height() / 4 * 3)
        self.right_window_cmd_out.setSizePolicy(sizePolicy)
        """
        self.right_window_cmd_out.setReadOnly(True)

        self.right_window_splitter = QSplitter(Qt.Vertical)
        self.right_window_splitter.addWidget(self.right_window)
        self.right_window_splitter.addWidget(self.right_window_cmd_out)
        self.right_window_splitter.addWidget(self.right_window_cmd_in)

        # Making the space above left and right window
        self.top_frame = QFrame(self)
        self.top_frame.setMaximumHeight(MainWindow.TOP_WINDOW_MAX_HEIGHT)

        # Adding a splitter
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.left_window_splitter)
        self.splitter.addWidget(self.right_window_splitter)

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