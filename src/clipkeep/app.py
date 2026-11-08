from __future__ import annotations

import sys
import os
import fcntl

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QApplication

from clipboard import Clipboard
from database import Database
from favorites import FavoritesRepository
from hotkeys import HotkeyBackend
from popup import Popup
from tray import Tray

# Prefer XDG_RUNTIME_DIR (per-user tmpfs, cleaned on logout) and fall back to ~/.local/share.
_RUNTIME_DIR = os.environ.get("XDG_RUNTIME_DIR") or os.path.join(
    os.path.expanduser("~"), ".local", "share", "clipkeep"
)
LOCK_FILE = os.path.join(_RUNTIME_DIR, "clipkeep.lock")


class App:
    def __init__(self) -> None:
        # Single instance check FIRST, before creating any UI/tray/hotkey objects.
        # If another instance already holds the lock, exit quietly (code 0) so that
        # autostart entries / systemd units launching us twice don't create a duplicate.
        self._lock_fd = None
        if not self._acquire_lock():
            print("clipkeep is already running; exiting this instance.", file=sys.stderr)
            sys.exit(0)

        self._qapp = QApplication.instance() or QApplication(sys.argv)
        QCoreApplication.setApplicationName("clipkeep")

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
        """Take an exclusive, non-blocking flock. True if we are the only instance.

        The lock is held for the lifetime of the process and released by the kernel
        when the process exits (even on crash or pkill), so there are no stale locks.
        The lock file is intentionally never deleted: unlinking it would let a new
        instance lock a fresh inode while the old one is still running.
        """
        try:
            os.makedirs(os.path.dirname(LOCK_FILE), exist_ok=True)
            fd = os.open(LOCK_FILE, os.O_CREAT | os.O_RDWR, 0o600)
        except OSError:
            # Can't create a lock file at all; don't block startup because of it.
            return True

        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(fd)
            return False

        self._lock_fd = fd
        return True

    def _toggle_popup(self) -> None:
        if self._popup.isVisible():
            self._popup.hide_popup()
        else:
            self._popup.show_popup()

    def _quit(self) -> None:
        self._tray.hide()
        self._hotkeys.stop()
        self._db.close()
        # The lock is released automatically when the process exits.
        self._qapp.quit()

    def exec(self) -> int:
        return self._qapp.exec()
