from __future__ import annotations

import sys
import os
import fcntl

from PyQt5.QtCore import QCoreApplication, QTimer
from PyQt5.QtWidgets import QApplication

from clipboard import Clipboard
from database import Database
from favorites import FavoritesRepository
from hotkeys import HotkeyBackend
from popup import Popup
from tray import Tray

LOCK_FILE = os.path.join(os.path.expanduser("~"), ".local", "share", "clipkeep", "clipkeep.lock")


class App:
    def __init__(self) -> None:
        self._qapp = QApplication.instance() or QApplication(sys.argv)
        QCoreApplication.setApplicationName("clipkeep")
        
        # Single instance check
        self._lock_fd = None
        self._is_primary = self._acquire_lock()
        
        self._db = Database()
        self._favorites = FavoritesRepository(self._db)
        self._clipboard = Clipboard()
        self._popup = Popup(self._clipboard, self._favorites)
        self._tray = Tray()
        self._hotkeys = HotkeyBackend()
        self._hotkeys.toggled.connect(self._toggle_popup)
        self._hotkeys.start()
        self._tray.showHideRequested.connect(self._toggle_popup)
        self._tray.quitRequested.connect(self._quit)
        self._tray.show()
        self._popup.hide_popup()
        
        self._qapp.setQuitOnLastWindowClosed(False)

    def _acquire_lock(self) -> bool:
        """Try to acquire a file lock. Returns True if successful (primary instance)."""
        lock_dir = os.path.dirname(LOCK_FILE)
        os.makedirs(lock_dir, exist_ok=True)
        
        try:
            self._lock_fd = os.open(LOCK_FILE, os.O_CREAT | os.O_RDWR)
            fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (IOError, OSError):
            return False

    def _toggle_popup(self) -> None:
        if self._popup.isVisible():
            self._popup.hide_popup()
        else:
            self._popup.show_popup()

    def _quit(self) -> None:
        self._tray.hide()
        self._hotkeys.stop()
        self._db.close()
        
        if self._lock_fd is not None:
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
                os.close(self._lock_fd)
                if os.path.exists(LOCK_FILE):
                    os.unlink(LOCK_FILE)
            except Exception:
                pass
        
        self._qapp.quit()

    def exec(self) -> int:
        return self._qapp.exec()