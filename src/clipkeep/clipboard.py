from __future__ import annotations

import base64
import collections
import hashlib
import io
import os
import re
from pathlib import Path
from typing import Any

from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication

from constants import MAX_RECENT_ITEMS, MAX_TEXT_LENGTH, MAX_IMAGE_SIZE


class ClipboardItem:
    def __init__(self, kind: str, value: Any, source: str = "") -> None:
        self.kind = kind
        self.value = value
        self.source = source
        self.timestamp = __import__("time").time()
        if kind == "text":
            self.hash = hashlib.sha256(value.encode("utf-8")).hexdigest()
        elif kind == "image":
            self.hash = hashlib.sha256(value.encode("utf-8")).hexdigest()
        else:
            self.hash = hashlib.sha256(str(value).encode("utf-8")).hexdigest()

    @property
    def display(self) -> str:
        if self.kind == "text":
            return self.value
        if self.kind == "url":
            return self.value
        if self.kind == "image":
            return "[Image]"
        return "[Unknown]"


class Clipboard(QObject):
    textChanged = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._clipboard = QApplication.clipboard()
        self._self_copy_guard = False
        self._recent: collections.deque[ClipboardItem] = collections.deque(maxlen=MAX_RECENT_ITEMS)
        self._last_hash = ""
        self._clipboard.dataChanged.connect(self._on_data_changed)
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_clipboard)
        self._poll_timer.start(400)
        self._temp_image_dir = Path.home() / ".local" / "share" / "clipkeep" / "images"
        self._temp_image_dir.mkdir(parents=True, exist_ok=True)

    @property
    def recent(self) -> list[ClipboardItem]:
        return list(self._recent)

    def _on_data_changed(self) -> None:
        self._check_text()
        self._check_image()

    def _poll_clipboard(self) -> None:
        if self._self_copy_guard:
            self._self_copy_guard = False
            return
        self._check_text()
        self._check_image()

    def _check_text(self) -> None:
        text = (self._clipboard.text() or "").strip()
        if not text:
            return
        if len(text) > MAX_TEXT_LENGTH:
            text = text[: MAX_TEXT_LENGTH]
        current_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if current_hash == self._last_hash:
            return
        self._last_hash = current_hash
        if self._recent and self._recent[0].hash == current_hash:
            return
        kind = "url" if _looks_like_url(text) else "text"
        item = ClipboardItem(kind=kind, value=text, source="clipboard")
        self._recent.appendleft(item)
        self.textChanged.emit(item)

    def _check_image(self) -> None:
        image = self._clipboard.image()
        if image.isNull():
            return
        if image.width() <= 0 or image.height() <= 0:
            return
        byte_count = image.byteCount()
        if byte_count > MAX_IMAGE_SIZE:
            return
        ba = image.constBits()
        if ba is None:
            return
        try:
            raw = bytes(ba[:byte_count])
        except Exception:
            return
        current_hash = hashlib.sha256(raw).hexdigest()
        if current_hash == self._last_hash:
            return
        self._last_hash = current_hash
        if self._recent and self._recent[0].hash == current_hash:
            return
        save_path = self._temp_image_dir / f"{current_hash}.png"
        if not save_path.exists():
            image.save(str(save_path), "PNG")
        item = ClipboardItem(kind="image", value=str(save_path), source="clipboard")
        self._recent.appendleft(item)
        self.textChanged.emit(item)

    def set_text(self, text: str) -> None:
        self._self_copy_guard = True
        self._last_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        self._clipboard.setText(text)

    def set_image(self, image_path: str) -> None:
        self._self_copy_guard = True
        image = QImage(image_path)
        if not image.isNull():
            self._clipboard.setImage(image)
            ba = image.constBits()
            if ba is not None:
                self._last_hash = hashlib.sha256(bytes(ba)).hexdigest()

    def set_item(self, item: ClipboardItem) -> None:
        if item.kind in ("text", "url"):
            self.set_text(item.value)
        elif item.kind == "image":
            self.set_image(item.value)


_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def _looks_like_url(text: str) -> bool:
    return bool(_URL_RE.match(text.strip()))
