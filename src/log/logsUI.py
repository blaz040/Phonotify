from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QMenuBar, QAction, QScrollBar
)
from PyQt5.QtGui import QFont, QTextCharFormat, QColor, QIcon
from PyQt5.QtCore import Qt, QTimer
from log.logAPI import LOG_PATH, init_log
import os
import shutil
import sys
from config import IS_LINUX, IS_WINDOWS, app_icon

TAG = "LOG UI"
log = init_log(tag=TAG)


class LogUI(QMainWindow):

    TITLE = "Live Logs"
    UPDATING_LOGS_WAIT_MS = 1000
    updating_logs = False

    def __init__(self):
        # Ensure a QApplication instance exists
        self.app = QApplication.instance() or QApplication(sys.argv)

        super().__init__()
        self.setWindowTitle(self.TITLE)
        self.resize(1300, 800)
        self.setWindowIcon(QIcon(str(app_icon)))

        # Timer for periodic log updates
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._timer_tick)
        self._read_lines = 0

        # Menu bar
        menubar = self.menuBar()
        clear_action = QAction("Clear Logs", self)
        clear_action.triggered.connect(self.clear_log)
        menubar.addAction(clear_action)

        move_action = QAction("Move to end", self)
        move_action.triggered.connect(self.move_to_bottom)
        menubar.addAction(move_action)

        # Text area
        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)
        self.text_area.setFont(QFont("Monospace", 10))
        self.text_area.document().setDefaultStyleSheet(
            "body { padding: 10px; }"
        )
        self.setCentralWidget(self.text_area)

        # Text formats for error / info colouring
        self._fmt_error = QTextCharFormat()
        self._fmt_error.setForeground(QColor("red"))

        self._fmt_info = QTextCharFormat()
        self._fmt_info.setForeground(QColor("blue"))

        self._fmt_normal = QTextCharFormat()  # default foreground

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def closeEvent(self, event):
        """Called when the user clicks the window's X button."""
        event.ignore()
        self.close_window()

    def _scrolled_down(self) -> bool:
        sb = self.text_area.verticalScrollBar()
        return sb.value() >= sb.maximum() - 4   # small tolerance

    def _timer_tick(self):
        """Slot connected to the QTimer; delegates to update_logs."""
        self.update_logs(self._read_lines)

    def _perform_cleanup(self):
        try:
            self.close()
            self.destroy()
        except Exception as e:
            log.error(f"Destroy failed: {e}")

    # ------------------------------------------------------------------ #
    # Public API (matches original LogUI interface)                       #
    # ------------------------------------------------------------------ #

    def scrolled_down(self) -> bool:
        return self._scrolled_down()

    def update_logs(self, readLines: int = 0):
        if not self.updating_logs:
            return

        was_at_bottom = self._scrolled_down()

        with open(LOG_PATH, "r") as f:
            for _ in range(readLines):
                f.readline()
            content = f.read()

        if content:
            lines = content.splitlines(keepends=True)
            cursor = self.text_area.textCursor()
            cursor.movePosition(cursor.End)

            for line in lines:
                if "ERROR" in line.upper():
                    cursor.insertText(line, self._fmt_error)
                else:
                    cursor.insertText(line, self._fmt_normal)

            readLines += len(lines)

        self._read_lines = readLines

        if was_at_bottom:
            self.move_to_bottom()

    def move_to_bottom(self):
        sb = self.text_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def clear_log(self):
        self.stop_updating_logs()
        self.text_area.clear()
        self._read_lines = 0
        with open(LOG_PATH, "w") as f:
            f.write("")
        self.start_updating_logs()

    def stop_updating_logs(self):
        if self.updating_logs:
            log.info("Stopped updating logs")
            self.updating_logs = False
            self._timer.stop()

    def start_updating_logs(self):
        if not self.updating_logs:
            log.info("Starting updating logs")
            self.updating_logs = True
            self.update_logs(self._read_lines)          # immediate first read
            self._timer.start(self.UPDATING_LOGS_WAIT_MS)

    def start(self):
        self.start_updating_logs()
        self.hide()
        self.app.exec_()

    def close_window(self):
        self.stop_updating_logs()
        self.hide()

    def show_window(self):
        self.show()
        self.raise_()
        self.move_to_bottom()
        self.start_updating_logs()

        if IS_LINUX:
            if shutil.which("wmctrl"):
                os.system(f"wmctrl -a '{self.TITLE}'")
            else:
                self.activateWindow()
        elif IS_WINDOWS:
            self.setWindowState(
                (self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive
            )
            self.activateWindow()

    def end(self):
        QTimer.singleShot(10, self._perform_cleanup)