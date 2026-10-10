from __future__ import annotations

import os

from PyQt5.QtCore import QSize, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu

from constants import APP_NAME


class Tray(QSystemTrayIcon):
    showHideRequested = pyqtSignal()
    quitRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Try to load icon from installed locations
        icon = QIcon.fromTheme(APP_NAME)
        if icon.isNull():
            icon = QIcon.fromTheme("edit-paste")
        if icon.isNull():
            # Fallback: create a simple clipboard icon
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor("#2a2a2a"))
            painter.setPen(QColor("#e0e0e0"))
            painter.drawRoundedRect(8, 8, 48, 48, 8, 8)
            painter.setPen(QColor("#888"))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "📋")
            painter.end()
            icon = QIcon(pixmap)
        
        self.setIcon(icon)
        self.setToolTip(f"{APP_NAME} - Lightweight clipboard manager")
        
        menu = QMenu()
        show_action = menu.addAction("Show / Hide")
        show_action.triggered.connect(self.showHideRequested.emit)
        menu.addSeparator()
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self.quitRequested.emit)
        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)
        
        # Make sure tray icon is visible
        self.setVisible(True)

    def _on_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick, QSystemTrayIcon.MiddleClick):
            self.showHideRequested.emit()
