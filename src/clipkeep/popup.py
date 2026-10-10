from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import QEvent, QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPalette, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTabBar,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from clipboard import ClipboardItem
from clipboard import Clipboard as ClipboardModule
from constants import APP_NAME  # noqa: F401
from favorites import FavoritesRepository


# --------------------------------------------------------------------------
# Layout constants
# --------------------------------------------------------------------------

POPUP_WIDTH = 420
WINDOW_MARGIN = 12
CARD_HEIGHT = 56
LIST_SPACING = 3
MAX_VISIBLE_ROWS = 7
MIN_VISIBLE_ROWS = 3


# ==========================================================================
# MINT DARK PALETTE
# ==========================================================================

# Main surfaces
BG_MAIN = "#1b1d1c"
BG_SECONDARY = "#202321"
BG_CARD = "#272a28"
BG_HOVER = "#303330"
BG_SELECTED = "#3a3d3a"

# Text
TXT_PRIMARY = "#e6e8e6"
TXT_SECONDARY = "#a5aaa5"
TXT_TERTIARY = "#707570"

# Accents
GOLD = "#ffd700"
BLUE = "#6aa9ff"

# Subtle Linux-Mint-like green.
# فقط برای focus / accentهای ظریف استفاده می‌شود.
MINT = "#9ccc65"


SCROLLBAR_STYLE = f"""
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: {BG_SELECTED};
    border-radius: 3px;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background: {TXT_TERTIARY};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0px;
    width: 0px;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QScrollBar:horizontal {{
    height: 0px;
}}
"""


# ==========================================================================
# CLIP CARD
# ==========================================================================

class ClipCard(QWidget):

    clicked = pyqtSignal(object)
    previewRequested = pyqtSignal(object)

    _STYLE = f"""
        QWidget#clipCard {{
            background: {BG_CARD};
            border-radius: 8px;
        }}

        QWidget#clipCard:hover {{
            background: {BG_HOVER};
        }}

        QWidget#clipCard[sel="true"] {{
            background: {BG_SELECTED};
        }}
    """

    def __init__(
        self,
        item: ClipboardItem,
        parent=None,
    ):
        super().__init__(parent)

        self.item = item
        self._selected = False

        self.setObjectName(
            "clipCard"
        )

        self.setAttribute(
            Qt.WA_StyledBackground,
            True,
        )

        self.setFixedHeight(
            CARD_HEIGHT
        )

        self.setCursor(
            Qt.PointingHandCursor
        )

        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            12,
            8,
            12,
            8,
        )

        layout.setSpacing(
            10
        )

        # ------------------------------------------------------------------
        # Icon
        # ------------------------------------------------------------------

        icon_label = QLabel()

        icon_label.setFixedSize(
            28,
            28,
        )

        icon_label.setAlignment(
            Qt.AlignCenter
        )

        if item.kind == "image":

            icon_label.setStyleSheet(
                f"""
                background: {BG_HOVER};
                border-radius: 6px;
                """
            )

            pix = QPixmap(
                item.value
            )

            if not pix.isNull():

                thumb = pix.scaled(
                    28,
                    28,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )

                icon_label.setPixmap(
                    thumb
                )

            else:

                icon_label.setText(
                    "IMG"
                )

                icon_label.setStyleSheet(
                    f"""
                    background: {BG_HOVER};
                    border-radius: 6px;
                    color: {TXT_TERTIARY};
                    font-size: 10px;
                    """
                )

        elif item.kind == "url":

            icon_label.setText(
                "🌐"
            )

            icon_label.setStyleSheet(
                f"""
                background: {BG_HOVER};
                border-radius: 6px;
                color: {BLUE};
                font-size: 14px;
                """
            )

        else:

            icon_label.setText(
                "Aa"
            )

            icon_label.setStyleSheet(
                f"""
                background: {BG_HOVER};
                border-radius: 6px;
                color: {TXT_SECONDARY};
                font-size: 12px;
                """
            )

        layout.addWidget(
            icon_label
        )

        # ------------------------------------------------------------------
        # Text
        # ------------------------------------------------------------------

        text = item.display

        self._one_line = " ".join(
            text[:400].split()
        )

        self.label = QLabel()

        self.label.setObjectName(
            "clipText"
        )

        self.label.setWordWrap(
            False
        )

        self.label.setTextFormat(
            Qt.PlainText
        )

        self.label.setStyleSheet(
            f"""
            color: {TXT_PRIMARY};
            font-size: 13px;
            background: transparent;
            """
        )

        self.label.setSizePolicy(
            QSizePolicy.Ignored,
            QSizePolicy.Preferred,
        )

        self.label.setToolTip(
            text
        )

        self._elide(
            280
        )

        content_layout = QVBoxLayout()

        content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        content_layout.setSpacing(
            2
        )

        content_layout.addWidget(
            self.label
        )

        layout.addLayout(
            content_layout,
            stretch=1,
        )

        # ------------------------------------------------------------------
        # Favorite button
        # ------------------------------------------------------------------

        self.star = QPushButton()

        self.star.setFixedSize(
            20,
            20,
        )

        self.star.setFlat(
            True
        )

        self.star.setFocusPolicy(
            Qt.NoFocus
        )

        self.star.setCursor(
            Qt.PointingHandCursor
        )

        self._update_star(
            False
        )

        layout.addWidget(
            self.star
        )

        self.setStyleSheet(
            self._STYLE
        )

    def _elide(
        self,
        width: int,
    ) -> None:

        fm = self.label.fontMetrics()

        self.label.setText(
            fm.elidedText(
                self._one_line,
                Qt.ElideRight,
                max(
                    width,
                    40,
                ),
            )
        )

    def set_selected(
        self,
        selected: bool,
    ) -> None:

        if self._selected == selected:
            return

        self._selected = selected

        self.setProperty(
            "sel",
            selected,
        )

        self.style().unpolish(
            self
        )

        self.style().polish(
            self
        )

        self.update()

    def _update_star(
        self,
        is_fav: bool,
    ) -> None:

        if is_fav:

            self.star.setText(
                "★"
            )

            color = GOLD

        else:

            self.star.setText(
                "☆"
            )

            color = TXT_TERTIARY

        self.star.setStyleSheet(
            f"""
            color: {color};
            font-size: 14px;
            background: transparent;
            border: none;
            padding: 0px;
            """
        )

    def resizeEvent(
        self,
        event,
    ) -> None:

        super().resizeEvent(
            event
        )

        self._elide(
            self.width()
            - 24
            - 28
            - 20
            - 20
        )

    def contextMenuEvent(
        self,
        event,
    ) -> None:

        event.accept()

    def mousePressEvent(
        self,
        event,
    ) -> None:

        if event.button() == Qt.RightButton:

            self.previewRequested.emit(
                self.item
            )

            event.accept()

            return

        super().mousePressEvent(
            event
        )

    def mouseReleaseEvent(
        self,
        event,
    ) -> None:

        if event.button() == Qt.LeftButton:

            self.clicked.emit(
                self.item
            )

        super().mouseReleaseEvent(
            event
        )


# ==========================================================================
# PREVIEW PANEL
# ==========================================================================

class PreviewPanel(QWidget):

    closed = pyqtSignal()

    def __init__(
        self,
        item: ClipboardItem,
        clipboard: ClipboardModule,
        parent=None,
    ):

        super().__init__(
            parent,
            Qt.Window,
        )

        self.item = item
        self._clipboard = clipboard
        self._drag_pos = None

        self.setWindowFlags(
            Qt.Window
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
        )

        self.setAttribute(
            Qt.WA_TranslucentBackground,
            True,
        )

        self.setFixedSize(
            POPUP_WIDTH,
            362,
        )

        root = QWidget(
            self
        )

        root.setObjectName(
            "previewRoot"
        )

        root.setStyleSheet(
            f"""
            QWidget#previewRoot {{
                background: {BG_SECONDARY};
                border: 1px solid {BG_HOVER};
                border-radius: 12px;
            }}

            QLabel#previewTitle {{
                color: {TXT_PRIMARY};
                font-weight: bold;
                font-size: 14px;
            }}

            QPushButton#previewClose {{
                background: transparent;
                color: {TXT_TERTIARY};
                border: none;
                border-radius: 6px;
                font-size: 14px;
                padding: 0px;
            }}

            QPushButton#previewClose:hover {{
                background: {BG_HOVER};
                color: {TXT_PRIMARY};
            }}

            QPushButton#previewBtn {{
                background: {BG_HOVER};
                color: {TXT_PRIMARY};
                border: 1px solid {BG_SELECTED};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }}

            QPushButton#previewBtn:hover {{
                background: {BG_SELECTED};
            }}

            QTextEdit {{
                background: {BG_CARD};
                color: {TXT_PRIMARY};
                border: 1px solid {BG_HOVER};
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }}

            QScrollArea {{
                background: {BG_CARD};
                border: none;
                border-radius: 8px;
            }}

            QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}

            {SCROLLBAR_STYLE}
            """
        )

        layout = QVBoxLayout(
            root
        )

        layout.setContentsMargins(
            20,
            16,
            20,
            20,
        )

        layout.setSpacing(
            12
        )

        # ------------------------------------------------------------------
        # Header
        # ------------------------------------------------------------------

        header = QHBoxLayout()

        title = QLabel(
            "Preview"
        )

        title.setObjectName(
            "previewTitle"
        )

        header.addWidget(
            title
        )

        header.addStretch(
            1
        )

        close_btn = QPushButton(
            "✕"
        )

        close_btn.setObjectName(
            "previewClose"
        )

        close_btn.setFlat(
            True
        )

        close_btn.setFixedSize(
            24,
            24,
        )

        close_btn.setCursor(
            Qt.PointingHandCursor
        )

        close_btn.setFocusPolicy(
            Qt.NoFocus
        )

        close_btn.clicked.connect(
            self.hide
        )

        header.addWidget(
            close_btn
        )

        layout.addLayout(
            header
        )

        # ------------------------------------------------------------------
        # Preview content
        # ------------------------------------------------------------------

        if item.kind == "image":

            scroll = QScrollArea()

            scroll.setWidgetResizable(
                True
            )

            scroll.setFrameShape(
                QFrame.NoFrame
            )

            img_label = QLabel()

            img_label.setAlignment(
                Qt.AlignCenter
            )

            pix = QPixmap(
                item.value
            )

            if not pix.isNull():

                img_label.setPixmap(
                    pix
                )

            scroll.setWidget(
                img_label
            )

            layout.addWidget(
                scroll,
                stretch=1,
            )

        else:

            text_edit = QTextEdit()

            text_edit.setPlainText(
                item.value
            )

            text_edit.setReadOnly(
                True
            )

            layout.addWidget(
                text_edit,
                stretch=1,
            )

        # ------------------------------------------------------------------
        # Buttons
        # ------------------------------------------------------------------

        btns = QHBoxLayout()

        btns.addStretch(
            1
        )

        copy_btn = QPushButton(
            "Copy"
        )

        copy_btn.setObjectName(
            "previewBtn"
        )

        copy_btn.setCursor(
            Qt.PointingHandCursor
        )

        copy_btn.clicked.connect(
            lambda:
            clipboard.set_item(
                item
            )
        )

        btns.addWidget(
            copy_btn
        )

        close_btn2 = QPushButton(
            "Close"
        )

        close_btn2.setObjectName(
            "previewBtn"
        )

        close_btn2.setCursor(
            Qt.PointingHandCursor
        )

        close_btn2.clicked.connect(
            self.hide
        )

        btns.addWidget(
            close_btn2
        )

        layout.addLayout(
            btns
        )

        outer = QVBoxLayout(
            self
        )

        outer.setContentsMargins(
            WINDOW_MARGIN,
            WINDOW_MARGIN,
            WINDOW_MARGIN,
            WINDOW_MARGIN,
        )

        outer.addWidget(
            root
        )

    def show_dialog(
        self,
        main_window_geometry=None,
    ) -> None:

        geo = (
            QApplication
            .primaryScreen()
            .availableGeometry()
        )

        if main_window_geometry:

            x = (
                main_window_geometry.left()
                - self.width()
                + 2 * WINDOW_MARGIN
                - 10
            )

            y = (
                main_window_geometry.top()
                + (
                    main_window_geometry.height()
                    - self.height()
                ) // 2
            )

            x = max(
                geo.left(),
                x,
            )

            y = max(
                geo.top(),
                min(
                    y,
                    geo.bottom()
                    - self.height(),
                ),
            )

        else:

            x = (
                geo.left()
                + (
                    geo.width()
                    - self.width()
                ) // 2
            )

            y = (
                geo.top()
                + (
                    geo.height()
                    - self.height()
                ) // 2
            )

        self.setGeometry(
            QRect(
                QPoint(
                    x,
                    y,
                ),
                self.size(),
            )
        )

        self.show()
        self.raise_()
        self.activateWindow()

    def hideEvent(
        self,
        event,
    ) -> None:

        super().hideEvent(
            event
        )

        self.closed.emit()

    def keyPressEvent(
        self,
        event,
    ) -> None:

        if event.key() == Qt.Key_Escape:

            self.hide()

            event.accept()

            return

        super().keyPressEvent(
            event
        )

    def mousePressEvent(
        self,
        event,
    ) -> None:

        if event.button() == Qt.LeftButton:

            self._drag_pos = (
                event.globalPos()
                - self.frameGeometry().topLeft()
            )

            event.accept()

    def mouseMoveEvent(
        self,
        event,
    ) -> None:

        if (
            self._drag_pos is not None
            and event.buttons()
            & Qt.LeftButton
        ):

            self.move(
                event.globalPos()
                - self._drag_pos
            )

            event.accept()

    def mouseReleaseEvent(
        self,
        event,
    ) -> None:

        self._drag_pos = None

        super().mouseReleaseEvent(
            event
        )


# ==========================================================================
# SEARCH BAR
# ==========================================================================

class SearchBar(QWidget):

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )

        layout = QHBoxLayout(
            self
        )

        layout.setContentsMargins(
            12,
            8,
            12,
            8,
        )

        layout.setSpacing(
            8
        )

        icon = QLabel(
            "🔍"
        )

        icon.setStyleSheet(
            f"""
            color: {TXT_TERTIARY};
            font-size: 13px;
            background: transparent;
            """
        )

        layout.addWidget(
            icon
        )

        self.field = QLineEdit()

        self.field.setPlaceholderText(
            "Search clipboard..."
        )

        self.field.setFixedHeight(
            32
        )

        self.field.setClearButtonEnabled(
            False
        )

        self.field.setStyleSheet(
            f"""
            QLineEdit {{
                background: {BG_CARD};
                color: {TXT_PRIMARY};
                border: 1px solid {BG_HOVER};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 13px;
            }}

            QLineEdit:focus {{
                border: 1px solid {MINT};
            }}
            """
        )

        if hasattr(
            QPalette,
            "PlaceholderText",
        ):

            pal = self.field.palette()

            pal.setColor(
                QPalette.PlaceholderText,
                QColor(
                    TXT_TERTIARY
                ),
            )

            self.field.setPalette(
                pal
            )

        layout.addWidget(
            self.field,
            stretch=1,
        )


# ==========================================================================
# EMPTY PAGE
# ==========================================================================

class _EmptyPage(QLabel):

    def __init__(
        self,
        text: str,
        parent=None,
    ):

        super().__init__(
            text,
            parent,
        )

        self.setAlignment(
            Qt.AlignCenter
        )

        self.setStyleSheet(
            f"""
            color: {TXT_TERTIARY};
            font-size: 13px;
            padding: 20px;
            background: transparent;
            """
        )


# ==========================================================================
# DOUBLE WIDTH TAB BAR
# ==========================================================================

class _EqualTabBar(QTabBar):

    """
    عرض طبیعی هر Tab را ۲ برابر می‌کند.

    نکته:
    عرض خود پنجره همچنان 420px باقی می‌ماند.
    """

    TAB_WIDTH_MULTIPLIER = 2

    def tabSizeHint(
        self,
        index: int,
    ) -> QSize:

        base = super().tabSizeHint(
            index
        )

        return QSize(
            base.width()
            * self.TAB_WIDTH_MULTIPLIER,
            base.height(),
        )

    def minimumTabSizeHint(
        self,
        index: int,
    ) -> QSize:

        return self.tabSizeHint(
            index
        )


# ==========================================================================
# TABS
# ==========================================================================

class _Tabs(QTabWidget):

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )

        bar = _EqualTabBar(
            self
        )

        bar.setExpanding(
            False
        )

        bar.setDrawBase(
            False
        )

        bar.setUsesScrollButtons(
            True
        )

        bar.setElideMode(
            Qt.ElideNone
        )

        bar.setFocusPolicy(
            Qt.NoFocus
        )

        bar.setCursor(
            Qt.PointingHandCursor
        )

        self.setTabBar(
            bar
        )


# ==========================================================================
# LIST STYLE
# ==========================================================================

_LIST_STYLE = f"""
    QListWidget {{
        background: {BG_MAIN};
        border: none;
        outline: none;
    }}

    QListWidget::item {{
        background: transparent;
        border-radius: 8px;
        padding: 0px;
    }}

    QListWidget::item:selected,
    QListWidget::item:hover {{
        background: transparent;
    }}
"""


# ==========================================================================
# POPUP
# ==========================================================================

class Popup(QWidget):

    def __init__(
        self,
        clipboard: ClipboardModule,
        favorites: FavoritesRepository,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self._clipboard = clipboard
        self._favorites = favorites

        self.setWindowFlags(
            Qt.Tool
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
        )

        self.setAttribute(
            Qt.WA_TranslucentBackground,
            True,
        )

        self.setFocusPolicy(
            Qt.StrongFocus
        )

        self._drag_pos = None

        self._preview_item: ClipboardItem | None = None

        self._all_items: list[ClipboardItem] = []

        self._preview_panel: PreviewPanel | None = None

        self._fav_count = 0

        # ------------------------------------------------------------------
        # Root
        # ------------------------------------------------------------------

        root = QWidget(
            self
        )

        root.setObjectName(
            "popupRoot"
        )

        root.setStyleSheet(
            f"""
            QWidget#popupRoot {{
                background: {BG_MAIN};
                border: 1px solid {BG_HOVER};
                border-radius: 12px;
            }}

            QLabel#popupTitle {{
                color: {TXT_PRIMARY};
            }}

            QPushButton#closeBtn {{
                background: transparent;
                color: {TXT_TERTIARY};
                border: none;
                border-radius: 6px;
                font-size: 14px;
                padding: 0px;
            }}

            QPushButton#closeBtn:hover {{
                background: {BG_HOVER};
                color: {TXT_PRIMARY};
            }}

            {SCROLLBAR_STYLE}
            """
        )

        vbox = QVBoxLayout(
            root
        )

        vbox.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        vbox.setSpacing(
            0
        )

        # ==================================================================
        # HEADER
        # ==================================================================

        header = QWidget()

        h = QHBoxLayout(
            header
        )

        h.setContentsMargins(
            16,
            12,
            14,
            4,
        )

        h.setSpacing(
            10
        )

        title = QLabel(
            "CLIPKEEP"
        )

        title.setObjectName(
            "popupTitle"
        )

        title_font = QFont(
            title.font()
        )

        title_font.setBold(
            True
        )

        title_font.setPixelSize(
            13
        )

        title_font.setLetterSpacing(
            QFont.AbsoluteSpacing,
            1.5,
        )

        title.setFont(
            title_font
        )

        h.addWidget(
            title
        )

        h.addStretch(
            1
        )

        close_btn = QPushButton(
            "✕"
        )

        close_btn.setObjectName(
            "closeBtn"
        )

        close_btn.setFlat(
            True
        )

        close_btn.setFixedSize(
            24,
            24,
        )

        close_btn.setCursor(
            Qt.PointingHandCursor
        )

        close_btn.setFocusPolicy(
            Qt.NoFocus
        )

        close_btn.clicked.connect(
            self.hide_popup
        )

        h.addWidget(
            close_btn
        )

        vbox.addWidget(
            header
        )

        # ==================================================================
        # SEARCH
        # ==================================================================

        self._search = SearchBar()

        self._search.field.textChanged.connect(
            self._filter_items
        )

        vbox.addWidget(
            self._search
        )

        # ==================================================================
        # TABS + CONTENT
        # ==================================================================

        content = QWidget()

        content_layout = QHBoxLayout(
            content
        )

        content_layout.setContentsMargins(
            12,
            0,
            12,
            12,
        )

        content_layout.setSpacing(
            0
        )

        self._tabs = _Tabs()

        self._tabs.setStyleSheet(
            f"""
            QTabWidget::pane {{
                border: none;
                background: transparent;
            }}

            QTabBar {{
                background: transparent;
            }}

            QTabBar::tab {{
                background: {BG_CARD};
                color: {TXT_SECONDARY};
                padding: 10px 0px;
                margin: 0px 0px 6px 0px;
                border: none;
                border-radius: 0px;
                text-align: center;
                font-size: 13px;
            }}

            QTabBar::tab:first {{
                border-top-left-radius: 6px;
                border-bottom-left-radius: 6px;
            }}

            QTabBar::tab:last {{
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                border-left: 1px solid {BG_HOVER};
            }}

            QTabBar::tab:hover {{
                background: {BG_HOVER};
            }}

            QTabBar::tab:selected {{
                background: {BG_SELECTED};
                color: {TXT_PRIMARY};
            }}

            QTabBar::scroller {{
                width: 0px;
            }}

            QTabBar QToolButton {{
                background: {BG_CARD};
                color: {TXT_SECONDARY};
                border: none;
                width: 20px;
                height: 28px;
            }}

            QTabBar QToolButton:hover {{
                background: {BG_HOVER};
                color: {TXT_PRIMARY};
            }}
            """
        )

        # ------------------------------------------------------------------
        # RECENT
        # ------------------------------------------------------------------

        self._recent_stack = QStackedWidget()

        self._recent_list = self._make_list()

        self._recent_stack.addWidget(
            self._recent_list
        )

        self._recent_empty = _EmptyPage(
            "No recent items"
        )

        self._recent_stack.addWidget(
            self._recent_empty
        )

        self._tabs.addTab(
            self._recent_stack,
            "Recent",
        )

        # ------------------------------------------------------------------
        # FAVORITES
        # ------------------------------------------------------------------

        self._fav_stack = QStackedWidget()

        self._fav_list = self._make_list()

        self._fav_stack.addWidget(
            self._fav_list
        )

        self._fav_empty = _EmptyPage(
            "No favorites"
        )

        self._fav_stack.addWidget(
            self._fav_empty
        )

        self._tabs.addTab(
            self._fav_stack,
            "Favorites",
        )

        content_layout.addWidget(
            self._tabs,
            stretch=1,
        )

        vbox.addWidget(
            content
        )

        # ==================================================================
        # SIGNALS
        # ==================================================================

        self._recent_list.itemClicked.connect(
            self._on_select
        )

        self._fav_list.itemClicked.connect(
            self._on_select
        )

        self._recent_list.setContextMenuPolicy(
            Qt.CustomContextMenu
        )

        self._recent_list.customContextMenuRequested.connect(
            self._on_context_menu
        )

        self._fav_list.setContextMenuPolicy(
            Qt.CustomContextMenu
        )

        self._fav_list.customContextMenuRequested.connect(
            self._on_context_menu
        )

        self._recent_list.currentItemChanged.connect(
            self._on_current_changed
        )

        self._fav_list.currentItemChanged.connect(
            self._on_current_changed
        )

        self._tabs.currentChanged.connect(
            self._on_tab_changed
        )

        # ==================================================================
        # OUTER
        # ==================================================================

        outer = QVBoxLayout(
            self
        )

        outer.setContentsMargins(
            WINDOW_MARGIN,
            WINDOW_MARGIN,
            WINDOW_MARGIN,
            WINDOW_MARGIN,
        )

        outer.addWidget(
            root
        )

        self.setFixedWidth(
            POPUP_WIDTH
        )

        QApplication.instance().installEventFilter(
            self
        )

    # ======================================================================
    # CONSTRUCTION HELPERS
    # ======================================================================

    def _make_list(
        self,
    ) -> QListWidget:

        lw = QListWidget()

        lw.setFrameShape(
            QFrame.NoFrame
        )

        lw.setSpacing(
            LIST_SPACING
        )

        lw.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        lw.setVerticalScrollMode(
            QListWidget.ScrollPerPixel
        )

        lw.setStyleSheet(
            _LIST_STYLE
        )

        return lw

    def _add_card(
        self,
        list_widget: QListWidget,
        item: ClipboardItem,
        is_fav: bool,
    ) -> None:

        qitem = QListWidgetItem()

        widget = ClipCard(
            item,
            list_widget,
        )

        widget._update_star(
            is_fav
        )

        widget.clicked.connect(
            lambda it, w=widget:
            self._on_card_clicked(
                it,
                w,
            )
        )

        widget.previewRequested.connect(
            lambda it, w=widget:
            self._on_card_preview(
                it,
                w,
            )
        )

        widget.star.clicked.connect(
            lambda _, it=item, w=widget:
            self._toggle_favorite(
                it,
                w,
            )
        )

        qitem.setSizeHint(
            QSize(
                1,
                CARD_HEIGHT,
            )
        )

        list_widget.addItem(
            qitem
        )

        list_widget.setItemWidget(
            qitem,
            widget,
        )

    def _active_list(
        self,
    ) -> QListWidget:

        if self._tabs.currentIndex() == 0:

            return self._recent_list

        return self._fav_list

    def _preview_open(
        self,
    ) -> bool:

        return (
            self._preview_panel is not None
            and self._preview_panel.isVisible()
        )

    # ======================================================================
    # POPULATE / REFRESH
    # ======================================================================

    def _populate_recent(
        self,
        text: str = "",
    ) -> None:

        q = (
            text.lower()
            if text
            else ""
        )

        recent = list(
            self._clipboard.recent
        )

        items = [
            it
            for it in recent
            if q in it.display.lower()
        ] if q else recent

        self._all_items = items

        lw = self._recent_list

        lw.setUpdatesEnabled(
            False
        )

        lw.clear()

        for item in items:

            self._add_card(
                lw,
                item,
                self._favorites.is_favorite(
                    item.value
                ),
            )

        lw.setUpdatesEnabled(
            True
        )

        if items:

            self._recent_stack.setCurrentWidget(
                lw
            )

            lw.setCurrentRow(
                0
            )

        else:

            self._recent_empty.setText(
                "No matches"
                if q
                else "No recent items"
            )

            self._recent_stack.setCurrentWidget(
                self._recent_empty
            )

    def _populate_favorites(
        self,
    ) -> None:

        fav_items = (
            self._favorites.list_all()
        )

        self._fav_count = len(
            fav_items
        )

        lw = self._fav_list

        lw.setUpdatesEnabled(
            False
        )

        lw.clear()

        for text in fav_items:

            item = ClipboardItem(
                kind="text",
                value=text,
                source="favorites",
            )

            self._add_card(
                lw,
                item,
                True,
            )

        lw.setUpdatesEnabled(
            True
        )

        if fav_items:

            self._fav_stack.setCurrentWidget(
                lw
            )

            lw.setCurrentRow(
                0
            )

        else:

            self._fav_stack.setCurrentWidget(
                self._fav_empty
            )

    def _fit_height(
        self,
    ) -> None:

        rows = max(
            self._fav_count,
            len(
                self._clipboard.recent
            ),
        )

        rows = max(
            MIN_VISIBLE_ROWS,
            min(
                MAX_VISIBLE_ROWS,
                rows,
            ),
        )

        height = (
            rows
            * (
                CARD_HEIGHT
                + LIST_SPACING
            )
            + LIST_SPACING
        )

        self._recent_stack.setFixedHeight(
            height
        )

        self._fav_stack.setFixedHeight(
            height
        )

        if self.isVisible():

            bottom = (
                self.geometry().bottom()
            )

            self.adjustSize()

            self.setFixedWidth(
                POPUP_WIDTH
            )

            self.move(
                self.x(),
                bottom
                - self.height()
                + 1,
            )

        else:

            self.adjustSize()

            self.setFixedWidth(
                POPUP_WIDTH
            )

    def refresh(
        self,
    ) -> None:

        self._populate_recent(
            self._search.field.text()
        )

        self._populate_favorites()

        self._fit_height()

    def _filter_items(
        self,
        text: str,
    ) -> None:

        current_tab = (
            self._tabs.currentIndex()
        )

        if current_tab == 1:

            return

        self._populate_recent(
            text
        )

    def _on_tab_changed(
        self,
        index: int,
    ) -> None:

        self.refresh()

    def _on_current_changed(
        self,
        current,
        previous,
    ) -> None:

        lw = self.sender()

        if not isinstance(
            lw,
            QListWidget,
        ):

            return

        for it, flag in (
            (previous, False),
            (current, True),
        ):

            if it is None:
                continue

            try:

                w = lw.itemWidget(
                    it
                )

            except RuntimeError:

                continue

            if isinstance(
                w,
                ClipCard,
            ):

                w.set_selected(
                    flag
                )

    # ======================================================================
    # SHOW / HIDE
    # ======================================================================

    def show_popup(
        self,
    ) -> None:

        self._close_preview()

        self._search.field.blockSignals(
            True
        )

        self._search.field.clear()

        self._search.field.blockSignals(
            False
        )

        self._tabs.blockSignals(
            True
        )

        self._tabs.setCurrentIndex(
            0
        )

        self._tabs.blockSignals(
            False
        )

        self.refresh()

        self.adjustSize()

        self.setFixedWidth(
            POPUP_WIDTH
        )

        geo = (
            QApplication
            .primaryScreen()
            .availableGeometry()
        )

        x = (
            geo.left()
            + geo.width()
            - self.width()
            - 20
        )

        y = (
            geo.bottom()
            - self.height()
            - 20
        )

        self.setGeometry(
            QRect(
                QPoint(
                    x,
                    y,
                ),
                self.size(),
            )
        )

        self.show()

        self.raise_()

        self.activateWindow()

        self._search.field.setFocus()

    def hide_popup(
        self,
    ) -> None:

        self._close_preview()

        self.hide()

    # ======================================================================
    # PREVIEW
    # ======================================================================

    def _close_preview(
        self,
    ) -> None:

        if self._preview_panel is not None:

            self._preview_panel.hide()

        self._preview_item = None

    def _on_preview_closed(
        self,
    ) -> None:

        self._preview_item = None

    def _open_preview(
        self,
        item: ClipboardItem,
    ) -> None:

        self._close_preview()

        if self._preview_panel is not None:

            self._preview_panel.deleteLater()

        panel = PreviewPanel(
            item,
            self._clipboard,
            self,
        )

        panel.closed.connect(
            self._on_preview_closed
        )

        self._preview_panel = panel

        self._preview_item = item

        panel.show_dialog(
            self.geometry()
        )

    def _on_card_preview(
        self,
        item: ClipboardItem,
        widget: ClipCard,
    ) -> None:

        self._open_preview(
            item
        )

    def _show_preview(
        self,
        item: QListWidgetItem,
        list_widget=None,
    ) -> None:

        if list_widget is None:

            list_widget = self.sender()

        if list_widget is None:

            return

        widget = list_widget.itemWidget(
            item
        )

        if isinstance(
            widget,
            ClipCard,
        ):

            self._open_preview(
                widget.item
            )

    def _on_context_menu(
        self,
        pos,
        list_widget=None,
    ) -> None:

        if list_widget is None:

            list_widget = self.sender()

        if list_widget is None:

            return

        item = list_widget.itemAt(
            pos
        )

        if item is None:

            return

        self._show_preview(
            item,
            list_widget,
        )

    # ======================================================================
    # ACTIONS
    # ======================================================================

    def _on_card_clicked(
        self,
        item: ClipboardItem,
        widget: ClipCard,
    ) -> None:

        self._clipboard.set_item(
            item
        )

    def _on_select(
        self,
        item: QListWidgetItem,
        list_widget=None,
    ) -> None:

        if list_widget is None:

            list_widget = self.sender()

        if list_widget is None:

            return

        widget = list_widget.itemWidget(
            item
        )

        if isinstance(
            widget,
            ClipCard,
        ):

            self._clipboard.set_item(
                widget.item
            )

    def _toggle_favorite(
        self,
        item: ClipboardItem,
        widget: ClipCard,
    ) -> None:

        is_fav = (
            self._favorites.is_favorite(
                item.value
            )
        )

        if is_fav:

            self._favorites.remove(
                item.value
            )

            widget._update_star(
                False
            )

        else:

            self._favorites.add(
                item.value
            )

            widget._update_star(
                True
            )

        if self._tabs.currentIndex() == 0:

            self._populate_favorites()

            self._fit_height()

    def _paste_current(
        self,
    ) -> None:

        lw = self._active_list()

        current = lw.currentItem()

        if current is not None:

            self._on_select(
                current,
                lw,
            )

    def _move_selection(
        self,
        delta: int,
    ) -> None:

        lw = self._active_list()

        count = lw.count()

        if count == 0:

            return

        row = lw.currentRow()

        row = (
            0
            if row < 0
            else max(
                0,
                min(
                    count - 1,
                    row + delta,
                ),
            )
        )

        lw.setCurrentRow(
            row
        )

        current = lw.currentItem()

        if current is not None:

            lw.scrollToItem(
                current
            )

    def _delete_current(
        self,
    ) -> None:

        if self._tabs.currentIndex() != 0:

            return

        current = (
            self._recent_list.currentItem()
        )

        if current is None:

            return

        widget = (
            self._recent_list.itemWidget(
                current
            )
        )

        if not isinstance(
            widget,
            ClipCard,
        ):

            return

        item = widget.item

        row = (
            self._recent_list.row(
                current
            )
        )

        store = self._clipboard._recent

        idx = next(
            (
                i
                for i, it in enumerate(store)
                if it is item
            ),
            None,
        )

        if idx is None:

            return

        if item.kind == "image":

            try:

                Path(
                    item.value
                ).unlink(
                    missing_ok=True
                )

            except Exception:

                pass

        del store[idx]

        self.refresh()

        count = (
            self._recent_list.count()
        )

        if count:

            self._recent_list.setCurrentRow(
                min(
                    row,
                    count - 1,
                )
            )

    # ======================================================================
    # EVENTS
    # ======================================================================

    def eventFilter(
        self,
        obj,
        event,
    ) -> bool:

        et = event.type()

        # ------------------------------------------------------------------
        # Outside click
        # ------------------------------------------------------------------

        if et == QEvent.MouseButtonPress:

            if (
                self.isVisible()
                and not self._preview_open()
                and not self.geometry().contains(
                    event.globalPos()
                )
            ):

                self.hide_popup()

                return True

            return False

        # ------------------------------------------------------------------
        # Search keyboard
        # ------------------------------------------------------------------

        if (
            et == QEvent.KeyPress
            and obj is self._search.field
            and self.isVisible()
        ):

            key = event.key()

            if key == Qt.Key_Up:

                self._move_selection(
                    -1
                )

                return True

            if key == Qt.Key_Down:

                self._move_selection(
                    1
                )

                return True

            if key in (
                Qt.Key_Return,
                Qt.Key_Enter,
            ):

                self._paste_current()

                return True

            if (
                key == Qt.Key_Delete
                and not self._search.field.text()
            ):

                self._delete_current()

                return True

        return False

    def mousePressEvent(
        self,
        event,
    ) -> None:

        if event.button() == Qt.LeftButton:

            self._drag_pos = (
                event.globalPos()
                - self.frameGeometry().topLeft()
            )

            event.accept()

    def mouseMoveEvent(
        self,
        event,
    ) -> None:

        if (
            self._drag_pos is not None
            and event.buttons()
            & Qt.LeftButton
        ):

            self.move(
                event.globalPos()
                - self._drag_pos
            )

            event.accept()

    def mouseReleaseEvent(
        self,
        event,
    ) -> None:

        self._drag_pos = None

    def keyPressEvent(
        self,
        event,
    ) -> None:

        key = event.key()

        if key == Qt.Key_Escape:

            if self._preview_open():

                self._close_preview()

            else:

                self.hide_popup()

            event.accept()

            return

        if key == Qt.Key_Delete:

            self._delete_current()

            event.accept()

            return

        if key in (
            Qt.Key_Return,
            Qt.Key_Enter,
        ):

            self._paste_current()

            event.accept()

            return

        if key == Qt.Key_Up:

            self._move_selection(
                -1
            )

            event.accept()

            return

        if key == Qt.Key_Down:

            self._move_selection(
                1
            )

            event.accept()

            return

        super().keyPressEvent(
            event
        )
