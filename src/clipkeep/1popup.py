from __future__ import annotations

from PyQt5.QtCore import QEvent, QPoint, QRect, Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QLineEdit,
    QTabWidget,
    QStackedWidget,
)

from clipboard import ClipboardItem
from clipboard import Clipboard as ClipboardModule
from constants import APP_NAME
from favorites import FavoritesRepository


class ClipCard(QWidget):
    clicked = pyqtSignal(object)
    previewRequested = pyqtSignal(object)

    def __init__(self, item: ClipboardItem, parent=None):
        super().__init__(parent)
        self.item = item
        self.setFixedHeight(56)
        self.setCursor(Qt.PointingHandCursor)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        icon_label = QLabel()
        icon_label.setFixedSize(28, 28)
        icon_label.setAlignment(Qt.AlignCenter)
        if item.kind == "image":
            icon_label.setStyleSheet("background: #1a1a1a; border-radius: 6px;")
            pix = QPixmap(item.value)
            if not pix.isNull():
                thumb = pix.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label.setPixmap(thumb)
            else:
                icon_label.setText("IMG")
                icon_label.setStyleSheet("background: #1a1a1a; border-radius: 6px; color: #666; font-size: 10px;")
        elif item.kind == "url":
            icon_label.setText("🌐")
            icon_label.setStyleSheet("background: #1a1a1a; border-radius: 6px; color: #4a9eff; font-size: 14px;")
        else:
            icon_label.setText("Aa")
            icon_label.setStyleSheet("background: #1a1a1a; border-radius: 6px; color: #888; font-size: 12px;")
        layout.addWidget(icon_label)
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)
        text = item.display
        self.label = QLabel(text)
        self.label.setWordWrap(False)
        self.label.setTextFormat(0)
        self.label.setStyleSheet("color: #e0e0e0; font-size: 13px;")
        fm = self.label.fontMetrics()
        elided = fm.elidedText(text, 1, 280)
        self.label.setText(elided)
        self.label.setToolTip(text)
        content_layout.addWidget(self.label)
        layout.addLayout(content_layout, stretch=1)
        self.star = QPushButton()
        self.star.setFixedSize(20, 20)
        self.star.setFlat(True)
        self.star.setCursor(Qt.PointingHandCursor)
        self._update_star(False)
        layout.addWidget(self.star)
        self.setStyleSheet(
            """
            QWidget {
                background: #141414;
                border-radius: 8px;
            }
            QWidget:hover {
                background: #1a1a1a;
            }
            """
        )

    def _update_star(self, is_fav: bool) -> None:
        if is_fav:
            self.star.setText("★")
            self.star.setStyleSheet("color: #ffd700; font-size: 14px; background: transparent;")
        else:
            self.star.setText("☆")
            self.star.setStyleSheet("color: #555; font-size: 14px; background: transparent;")

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.RightButton:
            self.previewRequested.emit(self.item)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.item)
        super().mouseReleaseEvent(event)


class PreviewPanel(QWidget):
    def __init__(self, item: ClipboardItem, clipboard: ClipboardModule, parent=None):
        super().__init__(parent, Qt.Window)
        self.item = item
        self._clipboard = clipboard
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(520, 380)
        root = QWidget(self)
        root.setObjectName("previewRoot")
        root.setStyleSheet(
            """
            QWidget#previewRoot {
                background: #0f0f0f;
                border-radius: 12px;
            }
            QPushButton {
                background: #1a1a1a;
                color: #e0e0e0;
                border: 1px solid #2a2a2a;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #2a2a2a;
            }
            QTextEdit {
                background: #141414;
                color: #e0e0e0;
                border: 1px solid #1a1a1a;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                line-height: 1.6;
            }
            QLabel {
                color: #e0e0e0;
            }
            """
        )
        layout = QVBoxLayout(root)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        header = QHBoxLayout()
        title = QLabel("Preview")
        title.setStyleSheet("color: #e0e0e0; font-weight: bold; font-size: 14px;")
        header.addWidget(title)
        header.addStretch(1)
        close_btn = QPushButton("✕")
        close_btn.setFlat(True)
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("color: #888; font-size: 14px; border: none;")
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)
        if item.kind == "image":
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setStyleSheet("background: #141414; border-radius: 8px;")
            img_label = QLabel()
            img_label.setAlignment(Qt.AlignCenter)
            pix = QPixmap(item.value)
            if not pix.isNull():
                img_label.setPixmap(pix)
            scroll.setWidget(img_label)
            layout.addWidget(scroll, stretch=1)
        else:
            text_edit = QTextEdit()
            text_edit.setPlainText(item.value)
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit, stretch=1)
        btns = QHBoxLayout()
        btns.addStretch(1)
        copy_btn = QPushButton("Copy")
        copy_btn.clicked.connect(lambda: clipboard.set_item(item))
        btns.addWidget(copy_btn)
        close_btn2 = QPushButton("Close")
        close_btn2.clicked.connect(self.close)
        btns.addWidget(close_btn2)
        layout.addLayout(btns)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.addWidget(root)

    def show_dialog(self, main_window_geometry=None) -> None:
        geo = QApplication.primaryScreen().availableGeometry()
        if main_window_geometry:
            x = main_window_geometry.left() - self.width() - 10
            y = main_window_geometry.top() + (main_window_geometry.height() - self.height()) // 2
            x = max(geo.left(), x)
            y = max(geo.top(), min(y, geo.bottom() - self.height()))
        else:
            x = geo.left() + (geo.width() - self.width()) // 2
            y = geo.top() + (geo.height() - self.height()) // 2
        self.setGeometry(QRect(QPoint(x, y), self.size()))
        self.show()
        self.raise_()
        self.activateWindow()


class SearchBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        icon = QLabel("🔍")
        icon.setStyleSheet("color: #666; font-size: 13px;")
        layout.addWidget(icon)
        self.field = QLineEdit()
        self.field.setPlaceholderText("Search clipboard...")
        self.field.setFixedHeight(32)
        self.field.setStyleSheet(
            """
            QLineEdit {
                background: #141414;
                color: #e0e0e0;
                border: 1px solid #1a1a1a;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #2a2a2a;
            }
            """
        )
        layout.addWidget(self.field, stretch=1)


class _EmptyPage(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("color: #555; padding: 20px;")


class Popup(QWidget):
    def __init__(self, clipboard: ClipboardModule, favorites: FavoritesRepository, parent=None):
        super().__init__(parent)
        self._clipboard = clipboard
        self._favorites = favorites
        self.setWindowFlags(
            Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.StrongFocus)
        self._drag_pos = None
        self._preview_item: ClipboardItem | None = None
        self._all_items: list[ClipboardItem] = []
        self._preview_panel = None
        QApplication.instance().installEventFilter(self)
        root = QWidget(self)
        root.setObjectName("popupRoot")
        root.setStyleSheet(
            """
            QWidget#popupRoot {
                background: #0a0a0a;
                border-radius: 12px;
            }
            QPushButton {
                border: none;
                padding: 4px;
            }
            """
        )
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        header = QWidget()
        header.setStyleSheet("background: #0a0a0a; border-top-left-radius: 12px; border-top-right-radius: 12px;")
        h = QHBoxLayout(header)
        h.setContentsMargins(14, 12, 14, 8)
        h.setSpacing(10)
        title = QLabel("CLIPKEEP")
        title.setStyleSheet("color: #e0e0e0; font-weight: bold; font-size: 13px; letter-spacing: 1.5px;")
        h.addWidget(title)
        h.addStretch(1)
        close_btn = QPushButton("✕")
        close_btn.setFlat(True)
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("color: #666; font-size: 14px; border-radius: 6px;")
        close_btn.clicked.connect(self.hide_popup)
        h.addWidget(close_btn)
        vbox.addWidget(header)
        search = SearchBar()
        search.field.textChanged.connect(self._filter_items)
        vbox.addWidget(search)
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self._tabs.setStyleSheet(
            """
            QTabWidget::pane { border: none; }
            QTabBar::tab {
                background: #141414;
                color: #888;
                padding: 6px 0px;
                min-width: 180px;
                border-radius: 6px;
            }
            QTabBar::tab:selected {
                background: #2a2a2a;
                color: #e0e0e0;
            }
            """
        )
        self._recent_stack = QStackedWidget()
        self._recent_list = QListWidget()
        self._recent_list.setFrameShape(QFrame.NoFrame)
        self._recent_list.setSpacing(3)
        self._recent_list.setStyleSheet(
            """
            QListWidget {
                background: #0a0a0a;
                border: none;
            }
            QListWidget::item {
                background: transparent;
                border-radius: 8px;
                padding: 0px;
            }
            """
        )
        self._recent_stack.addWidget(self._recent_list)
        self._recent_empty = _EmptyPage("No recent items")
        self._recent_stack.addWidget(self._recent_empty)
        self._tabs.addTab(self._recent_stack, "Recent")
        self._fav_stack = QStackedWidget()
        self._fav_list = QListWidget()
        self._fav_list.setFrameShape(QFrame.NoFrame)
        self._fav_list.setSpacing(3)
        self._fav_list.setStyleSheet(
            """
            QListWidget {
                background: #0a0a0a;
                border: none;
            }
            QListWidget::item {
                background: transparent;
                border-radius: 8px;
                padding: 0px;
            }
            """
        )
        self._fav_stack.addWidget(self._fav_list)
        self._fav_empty = _EmptyPage("No favorites")
        self._fav_stack.addWidget(self._fav_empty)
        self._tabs.addTab(self._fav_stack, "Favorites")
        content_layout.addWidget(self._tabs, stretch=1)
        vbox.addWidget(content)
        self._recent_list.itemClicked.connect(self._on_select)
        self._fav_list.itemClicked.connect(self._on_select)
        self._recent_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._recent_list.customContextMenuRequested.connect(self._on_context_menu)
        self._fav_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._fav_list.customContextMenuRequested.connect(self._on_context_menu)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.addWidget(root)
        self.setFixedWidth(420)

    def refresh(self) -> None:
        items = self._clipboard.recent
        self._all_items = items
        self._recent_list.clear()
        for item in items:
            qitem = QListWidgetItem()
            widget = ClipCard(item, self._recent_list)
            is_fav = self._favorites.is_favorite(item.value)
            widget._update_star(is_fav)
            widget.clicked.connect(lambda it, w=widget: self._on_card_clicked(it, w))
            widget.previewRequested.connect(lambda it, w=widget: self._on_card_preview(it, w))
            widget.star.clicked.connect(lambda _, it=item, w=widget: self._toggle_favorite(it, w))
            qitem.setSizeHint(widget.sizeHint())
            self._recent_list.addItem(qitem)
            self._recent_list.setItemWidget(qitem, widget)
        fav_items = self._favorites.list_all()
        self._fav_list.clear()
        if fav_items:
            for text in fav_items:
                item = ClipboardItem(kind="text", value=text, source="favorites")
                qitem = QListWidgetItem()
                widget = ClipCard(item, self._fav_list)
                widget._update_star(True)
                widget.clicked.connect(lambda it, w=widget: self._on_card_clicked(it, w))
                widget.previewRequested.connect(lambda it, w=widget: self._on_card_preview(it, w))
                widget.star.clicked.connect(lambda _, it=item, w=widget: self._toggle_favorite(it, w))
                qitem.setSizeHint(widget.sizeHint())
                self._fav_list.addItem(qitem)
                self._fav_list.setItemWidget(qitem, widget)
            self._fav_stack.setCurrentWidget(self._fav_list)
        else:
            self._fav_stack.setCurrentWidget(self._fav_empty)

    def _filter_items(self, text: str) -> None:
        current_tab = self._tabs.currentIndex()
        if current_tab == 1:
            return
        if not text:
            self._all_items = self._clipboard.recent
        else:
            q = text.lower()
            self._all_items = [it for it in self._clipboard.recent if q in it.display.lower()]
        self._recent_list.clear()
        for item in self._all_items:
            qitem = QListWidgetItem()
            widget = ClipCard(item, self._recent_list)
            is_fav = self._favorites.is_favorite(item.value)
            widget._update_star(is_fav)
            widget.clicked.connect(lambda it, w=widget: self._on_card_clicked(it, w))
            widget.previewRequested.connect(lambda it, w=widget: self._on_card_preview(it, w))
            widget.star.clicked.connect(lambda _, it=item, w=widget: self._toggle_favorite(it, w))
            qitem.setSizeHint(widget.sizeHint())
            self._recent_list.addItem(qitem)
            self._recent_list.setItemWidget(qitem, widget)

    def show_popup(self) -> None:
        self._preview_item = None
        if self._preview_panel is not None:
            self._preview_panel.hide()
        self.refresh()
        self.adjustSize()
        self.setFixedWidth(420)
        self._tabs.setCurrentIndex(0)
        geo = QApplication.primaryScreen().availableGeometry()
        x = geo.left() + geo.width() - self.width() - 20
        y = geo.bottom() - self.height() - 20
        self.setGeometry(QRect(QPoint(x, y), self.size()))
        self.show()
        self.raise_()
        self.activateWindow()

    def hide_popup(self) -> None:
        self.hide()

    def _on_card_clicked(self, item: ClipboardItem, widget: ClipCard) -> None:
        self._clipboard.set_item(item)

    def _on_card_preview(self, item: ClipboardItem, widget: ClipCard) -> None:
        self._preview_item = item
        if self._preview_panel is not None:
            self._preview_panel.close()
            self._preview_panel.deleteLater()
        self._preview_panel = PreviewPanel(item, self._clipboard, self)
        self._preview_panel.show_dialog(self.geometry())

    def _on_select(self, item: QListWidgetItem, list_widget=None) -> None:
        if list_widget is None:
            list_widget = self.sender()
        if list_widget is None:
            return
        widget = list_widget.itemWidget(item)
        if isinstance(widget, ClipCard):
            self._clipboard.set_item(widget.item)

    def _show_preview(self, item: QListWidgetItem, list_widget=None) -> None:
        if list_widget is None:
            list_widget = self.sender()
        if list_widget is None:
            return
        widget = list_widget.itemWidget(item)
        if isinstance(widget, ClipCard):
            self._preview_item = widget.item
            if self._preview_panel is not None:
                self._preview_panel.close()
                self._preview_panel.deleteLater()
            self._preview_panel = PreviewPanel(widget.item, self._clipboard, self)
            self._preview_panel.show_dialog(self.geometry())

    def _on_context_menu(self, pos, list_widget=None) -> None:
        if list_widget is None:
            list_widget = self.sender()
        if list_widget is None:
            return
        item = list_widget.itemAt(pos)
        if item is None:
            return
        self._show_preview(item, list_widget)

    def _toggle_favorite(self, item: ClipboardItem, widget: ClipCard) -> None:
        is_fav = self._favorites.is_favorite(item.value)
        if is_fav:
            self._favorites.remove(item.value)
            widget._update_star(False)
        else:
            self._favorites.add(item.value)
            widget._update_star(True)

    def _delete_current(self) -> None:
        current = self._recent_list.currentItem()
        if current is None:
            return
        row = self._recent_list.row(current)
        if row < 0 or row >= len(self._clipboard.recent):
            return
        item = self._clipboard.recent[row]
        if item.kind == "image":
            try:
                from pathlib import Path
                Path(item.value).unlink(missing_ok=True)
            except Exception:
                pass
        del self._clipboard._recent[row]
        self.refresh()

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.MouseButtonPress and not self.geometry().contains(event.globalPos()):
            if self.isVisible() and self._preview_item is None:
                self.hide_popup()
                return True
        return False

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        self._drag_pos = None

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            if self._preview_item is not None:
                self._preview_item = None
                if self._preview_panel is not None:
                    self._preview_panel.hide()
                self.show_popup()
            else:
                self.hide_popup()
            event.accept()
            return
        if event.key() == Qt.Key_Delete:
            self._delete_current()
            event.accept()
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            current = self._recent_list.currentItem()
            if current is not None:
                self._on_select(current, self._recent_list)
            event.accept()
            return
        super().keyPressEvent(event)
