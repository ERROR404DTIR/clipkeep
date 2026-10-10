import os
from dataclasses import dataclass
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from constants import DEFAULT_HOTKEY

@dataclass
class HotkeyError:
    message: str

class HotkeyBackend(QObject):
    toggled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._enabled = False
        self._error: HotkeyError | None = None
        self._insert_pressed = False
        self._insert_code = 118

    @property
    def error(self) -> HotkeyError | None:
        return self._error

    def start(self) -> None:
        if os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
            self._error = HotkeyError(
                "Wayland detected; global hotkeys are not supported."
            )
            return

        # Check if another instance is running
        lock_file = os.path.expanduser("~/.local/share/clipkeep/clipkeep.lock")
        if os.path.exists(lock_file):
            try:
                fd = os.open(lock_file, os.O_RDONLY)
                import fcntl
                # Try to acquire exclusive lock - if we can't, another instance is running
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                os.close(fd)
                # Lock acquired, so we're the primary instance
            except (IOError, OSError):
                # Another instance is already running
                self._error = HotkeyError(
                    "Clipkeep is already running. Global hotkeys disabled."
                )
                return

        try:
            from Xlib import XK, display
            d = display.Display()
            insert_keysym = XK.string_to_keysym("Insert")
            self._insert_code = d.keysym_to_keycode(insert_keysym)
            self._enabled = True
            self._poll_keys()
        except Exception as exc:
            self._error = HotkeyError(f"Xlib init failed: {exc}")

    def stop(self) -> None:
        self._enabled = False

    def _poll_keys(self) -> None:
        if not self._enabled:
            return

        try:
            from Xlib import display
            d = display.Display()
            mask = d.query_keymap()
            insert_down = bool(mask[self._insert_code // 8] & (1 << (self._insert_code % 8)))

            if insert_down and not self._insert_pressed:
                self._insert_pressed = True
                self.toggled.emit()
            elif not insert_down:
                self._insert_pressed = False
        except Exception:
            pass

        QTimer.singleShot(30, self._poll_keys)
