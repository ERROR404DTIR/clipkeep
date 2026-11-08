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
        self._display = None

    @property
    def error(self) -> HotkeyError | None:
        return self._error

    def start(self) -> None:
        if os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
            self._error = HotkeyError(
                "Wayland detected; global hotkeys are not supported."
            )
            return

        # Note: single-instance enforcement lives in App (app.py). Do not probe the
        # lock file here: flock() on a second file descriptor in the same process
        # conflicts with the lock App already holds and would disable hotkeys.

        try:
            from Xlib import XK, display
            # Open the X connection once and reuse it for every poll.
            self._display = display.Display()
            insert_keysym = XK.string_to_keysym("Insert")
            self._insert_code = self._display.keysym_to_keycode(insert_keysym)
            self._enabled = True
            self._poll_keys()
        except Exception as exc:
            self._error = HotkeyError(f"Xlib init failed: {exc}")

    def stop(self) -> None:
        self._enabled = False
        if self._display is not None:
            try:
                self._display.close()
            except Exception:
                pass
            self._display = None

    def _poll_keys(self) -> None:
        if not self._enabled or self._display is None:
            return

        try:
            mask = self._display.query_keymap()
            insert_down = bool(mask[self._insert_code // 8] & (1 << (self._insert_code % 8)))

            if insert_down and not self._insert_pressed:
                self._insert_pressed = True
                self.toggled.emit()
            elif not insert_down:
                self._insert_pressed = False
        except Exception:
            pass

        QTimer.singleShot(30, self._poll_keys)
