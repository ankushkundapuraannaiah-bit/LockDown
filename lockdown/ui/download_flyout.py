"""Lock Down Browser Interactive Download Flyout.
Modern popup anchored beneath the toolbar download button showing active progress,
speed, pause/cancel controls, and quick access to completed files.
"""

from typing import Optional

from lockdown.config import (
    COLOR_BLUE_BASE,
    COLOR_BLUE_BORDER,
    COLOR_CORAL_HOVER,
    COLOR_CORAL_PRIMARY,
    COLOR_IVORY_DARK,
    COLOR_IVORY_LIGHT,
    COLOR_IVORY_MUTED,
    COLOR_TEXT_DARK,
    COLOR_YELLOW_ACCENT,
    COLOR_YELLOW_BRIGHT,
    COLOR_YELLOW_SOFT,
)
from lockdown.download_manager import DownloadManager
from lockdown.qt_compat import (
    QEvent,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPoint,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    Qt,
    pyqtSignal,
)


class DownloadCardWidget(QFrame):
    """Card widget representing an individual download inside the flyout."""

    action_triggered = pyqtSignal()

    def __init__(self, item: dict, parent=None):
        super().__init__(parent)
        self.item_id = item["id"]
        self.item = item
        self.setObjectName("downloadFlyoutCard")
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"""
            QFrame#downloadFlyoutCard {{
                background-color: #FFFFFF;
                border: 1px solid {COLOR_YELLOW_ACCENT};
                border-radius: 10px;
                padding: 10px;
            }}
            QFrame#downloadFlyoutCard:hover {{
                border-color: {COLOR_CORAL_PRIMARY};
                background-color: #FFFDF7;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # Top row: icon + filename + state badge
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        icon_lbl = QLabel(self.item.get("icon", "📄"))
        icon_lbl.setStyleSheet("font-size: 20px; background: transparent;")
        top_row.addWidget(icon_lbl)

        name_col = QVBoxLayout()
        name_col.setSpacing(2)

        name_lbl = QLabel(self.item.get("filename", "download"))
        name_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {COLOR_TEXT_DARK};")
        name_lbl.setWordWrap(True)
        name_col.addWidget(name_lbl)

        # Meta string
        state = self.item.get("state", "completed")
        meta_text = ""
        if state == "in_progress":
            meta_text = f"{self.item.get('received_str', '')} of {self.item.get('total_str', '')}"
            if self.item.get("speed_str"):
                meta_text += f" • {self.item.get('speed_str')}"
            if self.item.get("eta_str"):
                meta_text += f" • {self.item.get('eta_str')}"
        elif state == "paused":
            meta_text = f"Paused • {self.item.get('received_str', '')} of {self.item.get('total_str', '')}"
        elif state == "completed":
            meta_text = f"Completed • {self.item.get('total_str', self.item.get('received_str', ''))}"
        elif state == "cancelled":
            meta_text = "Cancelled"
        elif state == "interrupted":
            meta_text = f"Failed: {self.item.get('error_message') or 'Interrupted'}"

        self.meta_lbl = QLabel(meta_text)
        self.meta_lbl.setStyleSheet(f"font-size: 11.5px; color: {COLOR_IVORY_MUTED};")
        name_col.addWidget(self.meta_lbl)

        top_row.addLayout(name_col, 1)

        layout.addLayout(top_row)

        # Progress bar for active / paused downloads
        if state in ("in_progress", "paused"):
            self.pbar = QProgressBar()
            self.pbar.setFixedHeight(5)
            self.pbar.setTextVisible(False)
            self.pbar.setRange(0, 100)
            self.pbar.setValue(self.item.get("progress_percent", 0))
            self.pbar.setStyleSheet(f"""
                QProgressBar {{
                    background: #F0F0F0;
                    border: none;
                    border-radius: 2px;
                }}
                QProgressBar::chunk {{
                    background: {COLOR_CORAL_PRIMARY};
                    border-radius: 2px;
                }}
            """)
            layout.addWidget(self.pbar)

        # Bottom action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        btn_row.addStretch()

        mgr = DownloadManager.get_instance()

        if state == "in_progress":
            pause_btn = QPushButton("⏸ Pause")
            self._style_btn(pause_btn)
            pause_btn.clicked.connect(lambda: (mgr.pause(self.item_id), self.action_triggered.emit()))
            btn_row.addWidget(pause_btn)

            cancel_btn = QPushButton("✕ Cancel")
            self._style_btn(cancel_btn, danger=True)
            cancel_btn.clicked.connect(lambda: (mgr.cancel(self.item_id), self.action_triggered.emit()))
            btn_row.addWidget(cancel_btn)

        elif state == "paused":
            resume_btn = QPushButton("▶ Resume")
            self._style_btn(resume_btn, primary=True)
            resume_btn.clicked.connect(lambda: (mgr.resume(self.item_id), self.action_triggered.emit()))
            btn_row.addWidget(resume_btn)

            cancel_btn = QPushButton("✕ Cancel")
            self._style_btn(cancel_btn, danger=True)
            cancel_btn.clicked.connect(lambda: (mgr.cancel(self.item_id), self.action_triggered.emit()))
            btn_row.addWidget(cancel_btn)

        elif state == "completed":
            if self.item.get("file_exists", True):
                open_btn = QPushButton("📂 Open")
                self._style_btn(open_btn, primary=True)
                open_btn.clicked.connect(lambda: mgr.open_file(self.item_id))
                btn_row.addWidget(open_btn)

                folder_btn = QPushButton("📁 Folder")
                self._style_btn(folder_btn)
                folder_btn.clicked.connect(lambda: mgr.show_in_folder(self.item_id))
                btn_row.addWidget(folder_btn)
            else:
                missing_lbl = QLabel("File deleted")
                missing_lbl.setStyleSheet("font-size: 11px; color: #8C8C8C; font-style: italic;")
                btn_row.addWidget(missing_lbl)

            rm_btn = QPushButton("✕")
            self._style_btn(rm_btn, danger=True)
            rm_btn.setToolTip("Remove from list")
            rm_btn.clicked.connect(lambda: (mgr.remove(self.item_id), self.action_triggered.emit()))
            btn_row.addWidget(rm_btn)

        else:
            rm_btn = QPushButton("✕ Remove")
            self._style_btn(rm_btn, danger=True)
            rm_btn.clicked.connect(lambda: (mgr.remove(self.item_id), self.action_triggered.emit()))
            btn_row.addWidget(rm_btn)

        layout.addLayout(btn_row)

    def _style_btn(self, btn: QPushButton, primary: bool = False, danger: bool = False):
        btn.setCursor(Qt.PointingHandCursor)
        if primary:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLOR_CORAL_PRIMARY};
                    color: #FFFFFF;
                    border: 1px solid {COLOR_CORAL_PRIMARY};
                    border-radius: 6px;
                    font-size: 11.5px;
                    font-weight: 700;
                    padding: 4px 10px;
                }}
                QPushButton:hover {{
                    background: {COLOR_CORAL_HOVER};
                }}
            """)
        elif danger:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: #8C8C8C;
                    border: 1px solid transparent;
                    border-radius: 6px;
                    font-size: 11.5px;
                    font-weight: 600;
                    padding: 4px 8px;
                }}
                QPushButton:hover {{
                    color: #CF1322;
                    background: rgba(245, 34, 45, 0.08);
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLOR_YELLOW_SOFT};
                    color: {COLOR_TEXT_DARK};
                    border: 1px solid {COLOR_YELLOW_ACCENT};
                    border-radius: 6px;
                    font-size: 11.5px;
                    font-weight: 700;
                    padding: 4px 10px;
                }}
                QPushButton:hover {{
                    background: {COLOR_YELLOW_BRIGHT};
                    color: {COLOR_CORAL_PRIMARY};
                }}
            """)


class LockDownDownloadFlyout(QWidget):
    """Floating dropdown flyout anchored below the navbar download button."""

    view_all_requested = pyqtSignal()

    def __init__(self, main_window, parent=None):
        super().__init__(parent or main_window, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.main_window = main_window
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.NoFocus)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # Outer Card Container
        self.card = QFrame(self)
        self.card.setObjectName("flyoutCard")
        self.card.setStyleSheet(f"""
            QFrame#flyoutCard {{
                background-color: #FFFFFF;
                border: 2px solid {COLOR_YELLOW_ACCENT};
                border-radius: 14px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
            }}
        """)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(14, 14, 14, 12)
        card_layout.setSpacing(10)

        # 1. Header Row
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        title_lbl = QLabel("📥 Downloads")
        title_lbl.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {COLOR_TEXT_DARK};")
        header_row.addWidget(title_lbl)

        self.active_badge = QLabel("0 active")
        self.active_badge.setStyleSheet(f"""
            background: {COLOR_CORAL_PRIMARY};
            color: #FFFFFF;
            font-size: 10.5px;
            font-weight: 800;
            padding: 2px 7px;
            border-radius: 8px;
        """)
        self.active_badge.hide()
        header_row.addWidget(self.active_badge)

        header_row.addStretch()

        # Open Downloads folder button
        folder_btn = QPushButton("📁")
        folder_btn.setToolTip("Open Downloads Folder")
        folder_btn.setCursor(Qt.PointingHandCursor)
        folder_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_YELLOW_SOFT};
                border: 1px solid {COLOR_YELLOW_ACCENT};
                border-radius: 8px;
                font-size: 13px;
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                background: {COLOR_YELLOW_BRIGHT};
            }}
        """)
        folder_btn.clicked.connect(lambda: DownloadManager.get_instance().open_downloads_folder())
        header_row.addWidget(folder_btn)

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setToolTip("Close")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 13px;
                font-weight: 700;
                color: #8C8C8C;
                padding: 4px 6px;
            }
            QPushButton:hover {
                color: #CF1322;
            }
        """)
        close_btn.clicked.connect(self.hide)
        header_row.addWidget(close_btn)

        card_layout.addLayout(header_row)

        # 2. Scrollable Items Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(8)

        self.scroll.setWidget(self.items_container)
        card_layout.addWidget(self.scroll, 1)

        # 3. Footer: "View all downloads" button
        footer_btn = QPushButton("View All Downloads (Ctrl+J)")
        footer_btn.setCursor(Qt.PointingHandCursor)
        footer_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_YELLOW_SOFT};
                border: 1.5px solid {COLOR_YELLOW_ACCENT};
                color: {COLOR_TEXT_DARK};
                border-radius: 8px;
                font-size: 12.5px;
                font-weight: 700;
                padding: 8px 14px;
            }}
            QPushButton:hover {{
                background: {COLOR_CORAL_PRIMARY};
                border-color: {COLOR_CORAL_PRIMARY};
                color: #FFFFFF;
            }}
        """)
        footer_btn.clicked.connect(self._on_view_all_clicked)
        card_layout.addWidget(footer_btn)

        root.addWidget(self.card)

        self.setFixedWidth(380)
        self.setFixedHeight(400)

    def _connect_signals(self):
        mgr = DownloadManager.get_instance()
        mgr.downloads_changed.connect(self.refresh_items)
        mgr.download_progress.connect(self._on_progress_update)

    def refresh_items(self):
        # Clear existing items
        while self.items_layout.count():
            w = self.items_layout.takeAt(0).widget()
            if w:
                w.deleteLater()

        mgr = DownloadManager.get_instance()
        downloads = mgr.get_downloads()
        active_count = mgr.get_active_count()

        if active_count > 0:
            self.active_badge.setText(f"{active_count} active")
            self.active_badge.show()
        else:
            self.active_badge.hide()

        if not downloads:
            empty_lbl = QLabel("No downloads yet")
            empty_lbl.setAlignment(Qt.AlignCenter)
            empty_lbl.setStyleSheet(f"font-size: 13px; color: {COLOR_IVORY_MUTED}; padding: 40px 0;")
            self.items_layout.addWidget(empty_lbl)
            return

        # Show up to 8 recent items
        for item in downloads[:8]:
            card = DownloadCardWidget(item, self)
            card.action_triggered.connect(self.refresh_items)
            self.items_layout.addWidget(card)

        self.items_layout.addStretch()

    def _on_progress_update(self, item_dict: dict):
        if not self.isVisible():
            return
        # Live refresh active cards if open
        self.refresh_items()

    def show_anchored(self, target_widget: QWidget):
        """Displays flyout anchored right beneath the target widget."""
        self.refresh_items()
        pos = target_widget.mapToGlobal(QPoint(target_widget.width() - self.width(), target_widget.height() + 6))
        self.move(pos)
        self.show()
        self.raise_()

    def _on_view_all_clicked(self):
        self.hide()
        self.view_all_requested.emit()
