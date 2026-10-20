"""Lock Down AI Mode Panel.
An intelligent browser side-panel powered by Google Gemini multimodal vision.
Allows Gemini to view the browser viewport, inspect page context, and deliver
step-by-step solutions to the user.
"""

from typing import Optional

from lockdown.config import (
    COLOR_BLUE_BASE,
    COLOR_BLUE_BORDER,
    COLOR_BLUE_DARK,
    COLOR_BLUE_DARKEST,
    COLOR_BLUE_SURFACE,
    COLOR_CORAL_HOVER,
    COLOR_CORAL_PRIMARY,
    COLOR_IVORY,
    COLOR_IVORY_DARK,
    COLOR_IVORY_LIGHT,
    COLOR_IVORY_MUTED,
    COLOR_YELLOW_ACCENT,
    COLOR_YELLOW_BRIGHT,
    COLOR_YELLOW_SOFT,
    load_settings,
    save_settings,
)
from lockdown.gemini_service import (
    DEFAULT_MODEL,
    SUPPORTED_MODELS,
    GeminiQueryWorker,
    GeminiService,
)
from lockdown.icons import get_icon
from lockdown.qt_compat import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QIcon,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPixmap,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    Qt,
    pyqtSignal,
)


class GeminiSetupDialog(QWidget):
    """Setup card to link Gemini API Key and select model."""

    account_linked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = GeminiService.get_instance()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Header
        title = QLabel("✨ Link Gemini Account")
        title.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {COLOR_IVORY_LIGHT};")
        layout.addWidget(title)

        desc = QLabel(
            "Connect your Google Gemini account to empower the browser with real-time visual reasoning, "
            "code problem solving, and intelligent page analysis."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"font-size: 12px; color: {COLOR_IVORY_DARK}; line-height: 1.4;")
        layout.addWidget(desc)

        # API Key input
        key_label = QLabel("Gemini API Key:")
        key_label.setStyleSheet(f"font-size: 11.5px; font-weight: 700; color: {COLOR_IVORY_LIGHT};")
        layout.addWidget(key_label)

        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.Password)
        self.key_input.setPlaceholderText("Paste AIzaSy... key from Google AI Studio")
        self.key_input.setText(self.service.get_api_key())
        self.key_input.setStyleSheet(f"""
            QLineEdit {{
                background: #FFFFFF;
                border: 1.5px solid {COLOR_YELLOW_ACCENT};
                border-radius: 8px;
                padding: 8px 12px;
                font-family: monospace;
                color: {COLOR_IVORY_LIGHT};
            }}
            QLineEdit:focus {{
                border-color: {COLOR_CORAL_PRIMARY};
            }}
        """)
        layout.addWidget(self.key_input)

        # Model selector
        model_label = QLabel("Active Vision Model:")
        model_label.setStyleSheet(f"font-size: 11.5px; font-weight: 700; color: {COLOR_IVORY_LIGHT};")
        layout.addWidget(model_label)

        self.model_combo = QComboBox()
        cur_model = self.service.get_model()
        for idx, m in enumerate(SUPPORTED_MODELS):
            self.model_combo.addItem(f"{m['name']} ({m['tag']})", m["id"])
            if m["id"] == cur_model:
                self.model_combo.setCurrentIndex(idx)
        self.model_combo.setStyleSheet(f"""
            QComboBox {{
                background: #FFFFFF;
                border: 1.5px solid {COLOR_YELLOW_ACCENT};
                border-radius: 8px;
                padding: 6px 10px;
                color: {COLOR_IVORY_LIGHT};
                font-weight: 600;
            }}
        """)
        layout.addWidget(self.model_combo)

        # Free API Key link button
        link_btn = QPushButton("🔑 Get Free Gemini Key (Google AI Studio)")
        link_btn.setCursor(Qt.PointingHandCursor)
        link_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {COLOR_CORAL_PRIMARY};
                font-size: 12px;
                font-weight: 700;
                text-align: left;
                padding: 4px 0;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        link_btn.clicked.connect(self._open_ai_studio)
        layout.addWidget(link_btn)

        # Status label
        self.status_lbl = QLabel("")
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setStyleSheet("font-size: 11.5px; font-weight: 600;")
        layout.addWidget(self.status_lbl)

        # Action button
        self.connect_btn = QPushButton("Connect & Verify Account")
        self.connect_btn.setCursor(Qt.PointingHandCursor)
        self.connect_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_CORAL_PRIMARY};
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                padding: 10px;
                font-weight: 800;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {COLOR_CORAL_HOVER};
            }}
        """)
        self.connect_btn.clicked.connect(self._verify_and_save)
        layout.addWidget(self.connect_btn)

    def _open_ai_studio(self):
        parent_win = self.window()
        if hasattr(parent_win, "add_tab"):
            parent_win.add_tab("https://aistudio.google.com/app/apikey", "Google AI Studio")

    def _verify_and_save(self):
        key = self.key_input.text().strip()
        if not key:
            self.status_lbl.setText("❌ Please enter a Gemini API Key.")
            self.status_lbl.setStyleSheet("color: #C0392B; font-weight: 700;")
            return

        self.status_lbl.setText("⏳ Verifying with Google Gemini...")
        self.status_lbl.setStyleSheet(f"color: {COLOR_IVORY_MUTED};")
        QApplication.processEvents()

        valid, msg, _ = self.service.validate_api_key(key)
        if valid:
            self.service.set_api_key(key)
            selected_model = self.model_combo.currentData()
            self.service.set_model(selected_model)
            self.status_lbl.setText("✅ " + msg)
            self.status_lbl.setStyleSheet("color: #27AE60; font-weight: 700;")
            self.account_linked.emit()
        else:
            self.status_lbl.setText("❌ " + msg)
            self.status_lbl.setStyleSheet("color: #C0392B; font-weight: 700;")


class LockDownAIPanel(QDockWidget):
    """Side panel for Gemini AI mode with real-time viewport analysis."""

    def __init__(self, browser_window):
        super().__init__("✨ Lock Down AI", browser_window)
        self.browser_window = browser_window
        self.service = GeminiService.get_instance()
        self.current_worker: Optional[GeminiQueryWorker] = None
        self.latest_pixmap: Optional[QPixmap] = None
        self.latest_b64: str = ""

        self.setObjectName("aiDockWidget")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable)
        self.setMinimumWidth(380)

        self._build_ui()
        self._refresh_account_status()

    def _build_ui(self):
        self.container = QWidget()
        self.container.setStyleSheet(f"background-color: {COLOR_BLUE_DARKEST};")
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(10)

        # ── Header Cluster ─────────────────────────────────────────────────
        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon("sparkles.svg").pixmap(22, 22))
        header.addWidget(icon_lbl)

        title_lbl = QLabel("AI Mode")
        title_lbl.setStyleSheet(f"font-size: 15px; font-weight: 900; color: {COLOR_IVORY_LIGHT}; letter-spacing: 0.5px;")
        header.addWidget(title_lbl)

        self.status_badge = QPushButton("🟡 Link Account")
        self.status_badge.setCursor(Qt.PointingHandCursor)
        self.status_badge.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_YELLOW_SOFT};
                border: 1px solid {COLOR_YELLOW_ACCENT};
                border-radius: 10px;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: 700;
                color: {COLOR_IVORY_DARK};
            }}
            QPushButton:hover {{
                border-color: {COLOR_CORAL_PRIMARY};
            }}
        """)
        self.status_badge.clicked.connect(self._toggle_settings_view)
        header.addWidget(self.status_badge)

        header.addStretch()

        self.clear_btn = QPushButton("🗑️")
        self.clear_btn.setToolTip("Clear Conversation")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setFixedSize(26, 26)
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                font-size: 13px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: {COLOR_YELLOW_SOFT};
            }}
        """)
        self.clear_btn.clicked.connect(self._clear_chat)
        header.addWidget(self.clear_btn)

        self.main_layout.addLayout(header)

        # ── Setup View (shown when unlinked or requested) ──────────────────
        self.setup_view = GeminiSetupDialog(self)
        self.setup_view.account_linked.connect(self._on_account_linked)
        self.main_layout.addWidget(self.setup_view)
        self.setup_view.hide()

        # ── Browser Viewport Context Card ──────────────────────────────────
        self.context_card = QFrame()
        self.context_card.setStyleSheet(f"""
            QFrame {{
                background: {COLOR_YELLOW_SOFT};
                border: 1.5px solid {COLOR_YELLOW_ACCENT};
                border-radius: 12px;
                padding: 8px;
            }}
        """)
        ctx_layout = QVBoxLayout(self.context_card)
        ctx_layout.setContentsMargins(6, 6, 6, 6)
        ctx_layout.setSpacing(6)

        ctrl_row = QHBoxLayout()
        self.view_browser_cb = QCheckBox("👁️ View Browser Viewport")
        self.view_browser_cb.setChecked(True)
        self.view_browser_cb.setStyleSheet(f"font-weight: 700; font-size: 12px; color: {COLOR_IVORY_LIGHT};")
        ctrl_row.addWidget(self.view_browser_cb)

        ctrl_row.addStretch()

        snap_btn = QPushButton("📸 Refresh")
        snap_btn.setToolTip("Re-capture current viewport")
        snap_btn.setCursor(Qt.PointingHandCursor)
        snap_btn.setStyleSheet(f"""
            QPushButton {{
                background: #FFFFFF;
                border: 1px solid {COLOR_YELLOW_ACCENT};
                border-radius: 8px;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: 700;
                color: {COLOR_IVORY_LIGHT};
            }}
            QPushButton:hover {{
                border-color: {COLOR_CORAL_PRIMARY};
            }}
        """)
        snap_btn.clicked.connect(self.capture_current_tab)
        ctrl_row.addWidget(snap_btn)
        ctx_layout.addLayout(ctrl_row)

        preview_row = QHBoxLayout()
        self.thumb_lbl = QLabel()
        self.thumb_lbl.setFixedSize(70, 44)
        self.thumb_lbl.setStyleSheet(f"background: #FFFFFF; border: 1px solid {COLOR_YELLOW_ACCENT}; border-radius: 6px;")
        self.thumb_lbl.setScaledContents(True)
        preview_row.addWidget(self.thumb_lbl)

        self.tab_info_lbl = QLabel("No active tab")
        self.tab_info_lbl.setWordWrap(True)
        self.tab_info_lbl.setStyleSheet(f"font-size: 11.5px; color: {COLOR_IVORY_DARK}; font-weight: 500;")
        preview_row.addWidget(self.tab_info_lbl, 1)

        ctx_layout.addLayout(preview_row)
        self.main_layout.addWidget(self.context_card)

        # ── Quick Action Chips ─────────────────────────────────────────────
        chips_layout = QHBoxLayout()
        chips_layout.setSpacing(6)
        chips = [
            ("📸 Analyze", "Analyze this page and explain its key elements and content."),
            ("💡 Solve Problem", "Identify and solve the problem or error shown on this screen step-by-step."),
            ("📝 Summarize", "Provide a concise editorial summary of this article/webpage."),
            ("💻 Explain Code", "Explain the code shown on this page and suggest fixes or improvements."),
        ]
        for label, prompt_text in chips:
            btn = QPushButton(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: #FFFFFF;
                    border: 1px solid {COLOR_YELLOW_ACCENT};
                    border-radius: 12px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: 700;
                    color: {COLOR_IVORY_LIGHT};
                }}
                QPushButton:hover {{
                    background: {COLOR_YELLOW_BRIGHT};
                    border-color: {COLOR_CORAL_PRIMARY};
                }}
            """)
            btn.clicked.connect(lambda _, p=prompt_text: self.send_prompt(p))
            chips_layout.addWidget(btn)
        self.main_layout.addLayout(chips_layout)

        # ── Chat & Solutions Scroll Area ───────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: 1px solid rgba(240, 192, 0, 0.3);
                border-radius: 12px;
            }}
        """)
        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        self.chat_layout.setSpacing(12)
        self.chat_layout.addStretch()
        self.scroll.setWidget(self.chat_container)
        self.main_layout.addWidget(self.scroll, 1)

        # ── Thinking / Loading Indicator ───────────────────────────────────
        self.loading_indicator = QLabel("✨ Gemini is analyzing the browser view and generating solutions...")
        self.loading_indicator.setStyleSheet(f"font-size: 11.5px; font-weight: 700; color: {COLOR_CORAL_PRIMARY};")
        self.loading_indicator.hide()
        self.main_layout.addWidget(self.loading_indicator)

        # ── Input Box Cluster ──────────────────────────────────────────────
        input_box = QFrame()
        input_box.setStyleSheet(f"""
            QFrame {{
                background: #FFFFFF;
                border: 1.5px solid {COLOR_YELLOW_ACCENT};
                border-radius: 14px;
                padding: 6px;
            }}
        """)
        in_layout = QVBoxLayout(input_box)
        in_layout.setContentsMargins(4, 4, 4, 4)
        in_layout.setSpacing(6)

        self.prompt_text = QTextEdit()
        self.prompt_text.setPlaceholderText("Ask Gemini about this webpage or request a solution... (Ctrl+Enter to send)")
        self.prompt_text.setMaximumHeight(70)
        self.prompt_text.setStyleSheet(f"""
            QTextEdit {{
                border: none;
                font-size: 13px;
                color: {COLOR_IVORY_LIGHT};
                background: transparent;
            }}
        """)
        in_layout.addWidget(self.prompt_text)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.send_btn = QPushButton("Send ➤")
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_CORAL_PRIMARY};
                color: #FFFFFF;
                font-weight: 800;
                font-size: 12.5px;
                border-radius: 12px;
                padding: 6px 14px;
                border: none;
            }}
            QPushButton:hover {{
                background: {COLOR_CORAL_HOVER};
            }}
        """)
        self.send_btn.clicked.connect(self._on_send_clicked)
        btn_row.addWidget(self.send_btn)
        in_layout.addLayout(btn_row)

        self.main_layout.addWidget(input_box)

        self.setWidget(self.container)

    def _refresh_account_status(self):
        if self.service.is_linked():
            model = self.service.get_model()
            self.status_badge.setText(f"🟢 Gemini Linked ({model})")
            self.status_badge.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(39, 174, 96, 0.15);
                    border: 1px solid #27AE60;
                    color: #1E8449;
                    font-size: 11px;
                    font-weight: 800;
                    border-radius: 10px;
                    padding: 3px 8px;
                }}
            """)
            self.setup_view.hide()
            self.context_card.show()
        else:
            self.status_badge.setText("🟡 Link Gemini Account")
            self.status_badge.setStyleSheet(f"""
                QPushButton {{
                    background: {COLOR_YELLOW_SOFT};
                    border: 1px solid {COLOR_YELLOW_ACCENT};
                    color: {COLOR_IVORY_DARK};
                    font-size: 11px;
                    font-weight: 800;
                    border-radius: 10px;
                    padding: 3px 8px;
                }}
            """)
            self.setup_view.show()

    def _toggle_settings_view(self):
        if self.setup_view.isVisible():
            self.setup_view.hide()
        else:
            self.setup_view.show()

    def _on_account_linked(self):
        self._refresh_account_status()
        self.capture_current_tab()

    def capture_current_tab(self):
        """Grabs screenshot and page info from the active browser tab."""
        tab_view = self.browser_window.current_browser()
        if not tab_view:
            self.tab_info_lbl.setText("No active tab")
            self.thumb_lbl.clear()
            self.latest_pixmap = None
            self.latest_b64 = ""
            return

        pix, b64 = self.service.capture_viewport(tab_view)
        self.latest_pixmap = pix
        self.latest_b64 = b64

        if pix and not pix.isNull():
            self.thumb_lbl.setPixmap(pix.scaled(70, 44, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))

        url_str = tab_view.url().toString()
        title_str = tab_view.current_title
        short_title = title_str[:30] + "..." if len(title_str) > 30 else title_str
        self.tab_info_lbl.setText(f"<b>{short_title}</b><br><span style='color:{COLOR_IVORY_MUTED}; font-size:10px;'>{url_str[:40]}</span>")

    def _clear_chat(self):
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_send_clicked(self):
        text = self.prompt_text.toPlainText().strip()
        if not text:
            return
        self.prompt_text.clear()
        self.send_prompt(text)

    def send_prompt(self, prompt: str):
        if not self.service.is_linked():
            self.setup_view.show()
            QMessageBox.information(
                self,
                "Link Gemini Account",
                "Please configure your Gemini API Key first to enable AI Mode.",
            )
            return

        # Make sure we have latest screenshot if enabled
        if self.view_browser_cb.isChecked():
            self.capture_current_tab()

        tab_view = self.browser_window.current_browser()
        page_url = tab_view.url().toString() if tab_view else ""
        page_title = tab_view.current_title if tab_view else ""
        img_b64 = self.latest_b64 if self.view_browser_cb.isChecked() else ""

        # Render user message card
        self._add_user_message(prompt, has_image=bool(img_b64))

        # Show loading
        self.loading_indicator.show()
        self.send_btn.setEnabled(False)

        # Worker
        self.current_worker = GeminiQueryWorker(
            prompt=prompt,
            image_base64=img_b64,
            page_url=page_url,
            page_title=page_title,
            page_text="",
            selected_text="",
        )
        self.current_worker.finished.connect(self._on_worker_finished)
        self.current_worker.error.connect(self._on_worker_error)
        self.current_worker.start()

    def _on_worker_finished(self, result: dict):
        self.loading_indicator.hide()
        self.send_btn.setEnabled(True)
        text = result.get("text", "")
        model = result.get("model", "")
        self._add_ai_solution(text, model)

    def _on_worker_error(self, err_msg: str):
        self.loading_indicator.hide()
        self.send_btn.setEnabled(True)
        self._add_error_card(err_msg)

    def _add_user_message(self, text: str, has_image: bool = False):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: #FFFFFF;
                border: 1px solid {COLOR_YELLOW_ACCENT};
                border-radius: 12px;
                padding: 10px 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        tag = QLabel(f"<b>You</b> {('• 📸 Viewport Attached' if has_image else '')}")
        tag.setStyleSheet(f"font-size: 11px; color: {COLOR_CORAL_PRIMARY}; font-weight: 700;")
        layout.addWidget(tag)

        msg = QLabel(text)
        msg.setWordWrap(True)
        msg.setStyleSheet(f"font-size: 13px; color: {COLOR_IVORY_LIGHT}; line-height: 1.4;")
        layout.addWidget(msg)

        # Insert before stretch
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, card)
        QApplication.processEvents()
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())

    def _add_ai_solution(self, text: str, model: str):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {COLOR_YELLOW_SOFT};
                border: 1.5px solid {COLOR_YELLOW_ACCENT};
                border-radius: 12px;
                padding: 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        header_row = QHBoxLayout()
        tag = QLabel(f"✨ <b>Gemini Solution</b> <span style='font-size: 10px; color: {COLOR_IVORY_MUTED};'>({model})</span>")
        tag.setStyleSheet(f"font-size: 12px; color: {COLOR_IVORY_LIGHT}; font-weight: 700;")
        header_row.addWidget(tag)

        header_row.addStretch()

        copy_btn = QPushButton("📋 Copy")
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: #FFFFFF;
                border: 1px solid {COLOR_YELLOW_ACCENT};
                border-radius: 6px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 700;
                color: {COLOR_IVORY_LIGHT};
            }}
            QPushButton:hover {{
                border-color: {COLOR_CORAL_PRIMARY};
            }}
        """)
        copy_btn.clicked.connect(lambda: self._copy_to_clipboard(text))
        header_row.addWidget(copy_btn)
        layout.addLayout(header_row)

        sol_edit = QTextEdit()
        sol_edit.setReadOnly(True)
        sol_edit.setMarkdown(text)
        sol_edit.setStyleSheet(f"""
            QTextEdit {{
                background: #FFFFFF;
                border: 1px solid rgba(240, 192, 0, 0.4);
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
                color: {COLOR_IVORY_LIGHT};
                line-height: 1.5;
            }}
        """)
        # Auto calculate reasonable height
        sol_edit.setMinimumHeight(120)
        sol_edit.setMaximumHeight(350)
        layout.addWidget(sol_edit)

        self.chat_layout.insertWidget(self.chat_layout.count() - 1, card)
        QApplication.processEvents()
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())

    def _add_error_card(self, err_text: str):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {{
                background: #FDEDEC;
                border: 1.5px solid #E74C3C;
                border-radius: 12px;
                padding: 10px 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(4, 4, 4, 4)
        err_lbl = QLabel(f"⚠️ <b>Gemini Error:</b> {err_text}")
        err_lbl.setWordWrap(True)
        err_lbl.setStyleSheet("color: #C0392B; font-size: 12px;")
        layout.addWidget(err_lbl)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, card)

    def _copy_to_clipboard(self, text: str):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "Copied", "Solution copied to clipboard!")
