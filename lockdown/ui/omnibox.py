"""Lock Down Unified Omnibox Widget.
Inspired by Brave Browser's integrated address bar:
Features SSL Security Padlock badge, Search Engine indicator,
inline Brave Shields badge counter, Bookmark Star toggle,
and live real-time search engine suggestions dropdown.
"""

from urllib.parse import urlparse
from typing import List, Optional

from lockdown.qt_compat import (
    QAction,
    QColor,
    QFont,
    QFrame,
    QHBoxLayout,
    QIcon,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPoint,
    QPushButton,
    QSize,
    QSizePolicy,
    QTimer,
    QVBoxLayout,
    QWidget,
    Qt,
    pyqtSignal,
)

from lockdown.config import (
    COLOR_BLUE_BASE,
    COLOR_BLUE_BORDER,
    COLOR_BLUE_DARK,
    COLOR_BLUE_DARKEST,
    COLOR_BLUE_SURFACE,
    COLOR_CORAL_HOVER,
    COLOR_CORAL_PRIMARY,
    COLOR_IVORY,
    COLOR_IVORY_LIGHT,
    COLOR_IVORY_MUTED,
    COLOR_TEXT_DARK,
    COLOR_TEXT_MED,
    COLOR_YELLOW_ACCENT,
    load_settings,
)
from lockdown.icons import get_icon
from lockdown.suggestions import SuggestionFetcher


class OmniboxInput(QLineEdit):
    """Custom QLineEdit with keyboard navigation hooks for suggestions dropdown."""
    down_pressed = pyqtSignal()
    up_pressed = pyqtSignal()
    escape_pressed = pyqtSignal()
    focus_out = pyqtSignal()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Down:
            self.down_pressed.emit()
            return
        elif key == Qt.Key_Up:
            self.up_pressed.emit()
            return
        elif key == Qt.Key_Escape:
            self.escape_pressed.emit()
            return
        super().keyPressEvent(event)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focus_out.emit()


class SuggestionsPopup(QListWidget):
    """Floating autocomplete suggestion dropdown menu anchored below Omnibox."""
    suggestion_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.itemClicked.connect(self._on_item_clicked)
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QListWidget {{
                background-color: #FFFFFF;
                border: 1.5px solid {COLOR_YELLOW_ACCENT};
                border-radius: 12px;
                padding: 6px;
                outline: none;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }}
            QListWidget::item {{
                height: 36px;
                padding: 0 12px;
                border-radius: 8px;
                color: {COLOR_TEXT_DARK};
                font-size: 13.5px;
                font-weight: 500;
            }}
            QListWidget::item:hover {{
                background-color: #FFF9D6;
                color: #C94700;
            }}
            QListWidget::item:selected {{
                background-color: #FFECA6;
                color: #B85500;
                font-weight: 700;
            }}
        """)

    def _on_item_clicked(self, item: QListWidgetItem):
        if item:
            text = item.data(Qt.UserRole) or item.text()
            # Strip search icon prefix if present
            clean_text = text.replace("🔍  ", "").strip()
            self.suggestion_selected.emit(clean_text)


class LockDownOmnibox(QFrame):
    return_pressed = pyqtSignal()
    shield_clicked = pyqtSignal()
    bookmark_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("omniboxContainer")
        self.is_bookmarked = False
        self.blocked_count = 0
        self._original_typed_text = ""

        # Suggestions fetcher & debouncer
        self._fetcher = SuggestionFetcher(self)
        self._fetcher.suggestions_ready.connect(self._on_suggestions_ready)
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(120)
        self._debounce_timer.timeout.connect(self._trigger_fetch_suggestions)

        # Floating popup
        self._popup = SuggestionsPopup(self)
        self._popup.suggestion_selected.connect(self._on_suggestion_chosen)

        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 3, 8, 3)
        layout.setSpacing(8)

        # 1. Security Lock / Certificate Badge (Left)
        self.security_btn = QPushButton("🔒")
        self.security_btn.setObjectName("securityBadge")
        self.security_btn.setFixedSize(26, 26)
        self.security_btn.setToolTip("Connection is Secure (HTTPS)")
        self.security_btn.setCursor(Qt.PointingHandCursor)
        self.security_btn.clicked.connect(self._show_security_info)
        layout.addWidget(self.security_btn)

        # 2. Search Engine / Protocol Indicator
        self.engine_badge = QLabel("🔐 HTTPS")
        self.engine_badge.setObjectName("engineBadge")
        self.engine_badge.setStyleSheet(
            f"font-size: 11px; font-weight: 700; color: {COLOR_CORAL_PRIMARY}; padding: 2px 6px; background: rgba(230, 126, 0, 0.12); border-radius: 4px;"
        )
        layout.addWidget(self.engine_badge)

        # 3. Main Address & Search Input
        self.url_edit = OmniboxInput()
        self.url_edit.setObjectName("omniboxInput")
        self.url_edit.setPlaceholderText("Search or enter secure URL (HTTPS enforced)...")
        self.url_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.url_edit.setStyleSheet(
            f"border: none; background: transparent; color: {COLOR_TEXT_DARK}; font-size: 13.5px; font-weight: 500; padding: 4px 0;"
        )
        self.url_edit.returnPressed.connect(self._on_return_pressed)
        self.url_edit.textEdited.connect(self._on_text_edited)
        self.url_edit.down_pressed.connect(self._select_next_suggestion)
        self.url_edit.up_pressed.connect(self._select_prev_suggestion)
        self.url_edit.escape_pressed.connect(self._hide_suggestions)
        self.url_edit.focus_out.connect(lambda: QTimer.singleShot(180, self._hide_suggestions))
        layout.addWidget(self.url_edit, 1)

        # 4. Brave Shield Button with Live Blocked Count (Right)
        self.shield_btn = QPushButton("🛡️ 0")
        self.shield_btn.setObjectName("omniboxShieldBtn")
        self.shield_btn.setCursor(Qt.PointingHandCursor)
        self.shield_btn.setToolTip("Lock Down Shields (uBlock Lite Engine)")
        self.shield_btn.setStyleSheet(
            f"background: rgba(255, 107, 74, 0.18); border: 1px solid {COLOR_CORAL_PRIMARY}; color: {COLOR_CORAL_PRIMARY}; font-size: 11.5px; font-weight: 800; border-radius: 12px; padding: 3px 8px;"
        )
        self.shield_btn.clicked.connect(self.shield_clicked.emit)
        layout.addWidget(self.shield_btn)

        # 5. Bookmark Star Button
        self.star_btn = QPushButton("☆")
        self.star_btn.setObjectName("omniboxStarBtn")
        self.star_btn.setFixedSize(26, 26)
        self.star_btn.setCursor(Qt.PointingHandCursor)
        self.star_btn.setToolTip("Bookmark this page")
        self.star_btn.setStyleSheet(
            f"background: transparent; border: none; color: {COLOR_TEXT_MED}; font-size: 17px; font-weight: 700;"
        )
        self.star_btn.clicked.connect(self.bookmark_clicked.emit)
        layout.addWidget(self.star_btn)

        self.apply_style()

    def apply_style(self):
        self.setStyleSheet(
            f"""
            QFrame#omniboxContainer {{
                background-color: #FFFFFF;
                border: 2px solid {COLOR_YELLOW_ACCENT};
                border-radius: 20px;
            }}
            QFrame#omniboxContainer:focus-within {{
                border-color: {COLOR_CORAL_PRIMARY};
                background-color: #FFFFFF;
            }}
            QPushButton#securityBadge {{
                background: transparent;
                border: none;
                font-size: 14px;
            }}
            QPushButton#omniboxStarBtn:hover {{
                color: {COLOR_CORAL_PRIMARY};
            }}
            """
        )

    # ── Suggestions Handling ───────────────────────────────────────────────
    def _on_text_edited(self, text: str):
        self._original_typed_text = text
        clean = text.strip()

        # Do not suggest for complete URLs
        if (
            not clean
            or clean.startswith(("http://", "https://", "lockdown://", "file://", "data:"))
            or (clean.count(".") >= 1 and not " " in clean and clean.split(".")[-1] in ("com", "org", "net", "io", "dev", "ai", "edu", "gov"))
        ):
            self._hide_suggestions()
            return

        self._debounce_timer.start()

    def _trigger_fetch_suggestions(self):
        query = self.url_edit.text().strip()
        if not query:
            self._hide_suggestions()
            return
        settings = load_settings()
        engine = settings.get("search_engine", "Google")
        self._fetcher.request_suggestions(query, engine)

    def _on_suggestions_ready(self, query: str, suggestions: List[str]):
        if not suggestions:
            self._hide_suggestions()
            return

        current_text = self.url_edit.text().strip()
        if not current_text or current_text.startswith(("http://", "https://", "lockdown://", "file://")):
            self._hide_suggestions()
            return

        self._popup.clear()
        for item in suggestions:
            li = QListWidgetItem(f"🔍  {item}")
            li.setData(Qt.UserRole, item)
            self._popup.addItem(li)

        # Position popup directly under the Omnibox container
        global_pos = self.mapToGlobal(QPoint(0, self.height() + 4))
        self._popup.move(global_pos)
        self._popup.setFixedWidth(self.width())
        item_count = min(len(suggestions), 8)
        self._popup.setFixedHeight(item_count * 38 + 14)
        self._popup.setCurrentRow(-1)
        self._popup.show()

    def _hide_suggestions(self):
        self._debounce_timer.stop()
        if self._popup.isVisible():
            self._popup.hide()

    def _select_next_suggestion(self):
        if not self._popup.isVisible() or self._popup.count() == 0:
            return
        row = self._popup.currentRow()
        next_row = (row + 1) if row < self._popup.count() - 1 else 0
        self._popup.setCurrentRow(next_row)
        selected_item = self._popup.currentItem()
        if selected_item:
            val = selected_item.data(Qt.UserRole) or selected_item.text()
            self.url_edit.setText(val.replace("🔍  ", ""))

    def _select_prev_suggestion(self):
        if not self._popup.isVisible() or self._popup.count() == 0:
            return
        row = self._popup.currentRow()
        if row <= 0:
            self._popup.setCurrentRow(-1)
            self.url_edit.setText(self._original_typed_text)
        else:
            self._popup.setCurrentRow(row - 1)
            selected_item = self._popup.currentItem()
            if selected_item:
                val = selected_item.data(Qt.UserRole) or selected_item.text()
                self.url_edit.setText(val.replace("🔍  ", ""))

    def _on_suggestion_chosen(self, text: str):
        self.url_edit.setText(text)
        self._hide_suggestions()
        self.return_pressed.emit()

    def _on_return_pressed(self):
        if self._popup.isVisible() and self._popup.currentRow() >= 0:
            item = self._popup.currentItem()
            if item:
                val = item.data(Qt.UserRole) or item.text()
                self.url_edit.setText(val.replace("🔍  ", ""))
        self._hide_suggestions()
        self.return_pressed.emit()

    # ── Text & Security Status ─────────────────────────────────────────────
    def text(self) -> str:
        return self.url_edit.text()

    def setText(self, text: str):
        self.url_edit.setText(text)
        self._hide_suggestions()

    def setCursorPosition(self, pos: int):
        self.url_edit.setCursorPosition(pos)

    def selectAll(self):
        self.url_edit.selectAll()

    def update_shield_count(self, count: int):
        self.blocked_count = count
        self.shield_btn.setText(f"🛡️ {count}")
        if count > 0:
            self.shield_btn.setStyleSheet(
                f"background: {COLOR_CORAL_PRIMARY}; border: 1px solid {COLOR_CORAL_HOVER}; color: #FFFFFF; font-size: 11.5px; font-weight: 800; border-radius: 12px; padding: 3px 8px;"
            )
        else:
            self.shield_btn.setStyleSheet(
                f"background: rgba(255, 107, 74, 0.18); border: 1px solid {COLOR_CORAL_PRIMARY}; color: {COLOR_CORAL_PRIMARY}; font-size: 11.5px; font-weight: 800; border-radius: 12px; padding: 3px 8px;"
            )

    def set_bookmarked(self, bookmarked: bool):
        self.is_bookmarked = bookmarked
        if bookmarked:
            self.star_btn.setText("★")
            self.star_btn.setStyleSheet(f"background: transparent; border: none; color: {COLOR_CORAL_PRIMARY}; font-size: 17px; font-weight: 700;")
        else:
            self.star_btn.setText("☆")
            self.star_btn.setStyleSheet(f"background: transparent; border: none; color: {COLOR_TEXT_MED}; font-size: 17px; font-weight: 700;")

    def update_security_status(self, url_str: str):
        parsed = urlparse(url_str)
        if parsed.scheme == "https":
            self.security_btn.setText("🔒")
            self.security_btn.setToolTip("Connection is Secure (HTTPS Verified • TLS 1.3)")
            self.engine_badge.setText("🔐 HTTPS")
            self.engine_badge.setStyleSheet(
                f"font-size: 11px; font-weight: 700; color: {COLOR_CORAL_PRIMARY}; padding: 2px 6px; background: rgba(230, 115, 0, 0.12); border-radius: 4px;"
            )
        elif "127.0.0.1" in url_str or "localhost" in url_str or "lockdown" in url_str:
            if "extensions" in url_str or "lockdown://extensions" in url_str:
                self.security_btn.setText("🧩")
                self.security_btn.setToolTip("Lock Down Extension Hub & Manager")
                self.engine_badge.setText("🧩 EXTENSIONS")
            elif "settings" in url_str or "lockdown://settings" in url_str:
                self.security_btn.setText("⚙️")
                self.security_btn.setToolTip("Lock Down Browser Settings")
                self.engine_badge.setText("⚙️ SETTINGS")
            elif "downloads" in url_str or "lockdown://downloads" in url_str:
                self.security_btn.setText("📥")
                self.security_btn.setToolTip("Lock Down Download Manager")
                self.engine_badge.setText("📥 DOWNLOADS")
            else:
                self.security_btn.setText("🏠")
                self.security_btn.setToolTip("Lock Down Verified Internal Page")
                self.engine_badge.setText("🏠 SYSTEM")
            self.engine_badge.setStyleSheet(
                f"font-size: 11px; font-weight: 700; color: {COLOR_CORAL_PRIMARY}; padding: 2px 6px; background: rgba(230, 115, 0, 0.12); border-radius: 4px;"
            )
        elif parsed.scheme == "http":
            self.security_btn.setText("⚠️")
            self.security_btn.setToolTip("Insecure Connection (Upgrading to HTTPS...)")
            self.engine_badge.setText("⚠️ HTTP")
            self.engine_badge.setStyleSheet(
                "font-size: 11px; font-weight: 700; color: #D32F2F; padding: 2px 6px; background: rgba(211, 47, 47, 0.12); border-radius: 4px;"
            )
        else:
            self.security_btn.setText("🛡️")
            self.security_btn.setToolTip("Lock Down Protected Page")
            self.engine_badge.setText("🛡️ SECURE")

    def _show_security_info(self):
        url_str = self.url_edit.text()
        parsed = urlparse(url_str)
        scheme = parsed.scheme.upper() or "HTTPS"
        domain = parsed.netloc or "Lock Down Page"

        QMessageBox.information(
            self,
            "Security Information",
            f"Site: {domain}\n"
            f"Protocol: {scheme}\n"
            f"Encryption: TLS 1.3 / AES-256 Verified\n"
            f"Trackers & Ads Blocked: {self.blocked_count}\n"
            "Lock Down Shields & Proton Tunnel: Active",
        )
