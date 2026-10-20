"""Lock Down Main Browser Window.
Redesigned with Brave-style integrated Omnibox (inline Shield badge & SSL lock),
Flow sidebar, Zen Focus Mode, and Proton VPN tunnel.
"""

from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from lockdown.qt_compat import (
    QAction,
    QApplication,
    QDockWidget,
    QEvent,
    QHBoxLayout,
    QIcon,
    QKeySequence,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPoint,
    QPushButton,
    QSize,
    QSizePolicy,
    QStatusBar,
    QTabBar,
    QTabWidget,
    QToolBar,
    QUrl,
    QVBoxLayout,
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
    QWidget,
    Qt,
)

from lockdown.blocker import ShieldRequestInterceptor, ShieldStats
from lockdown.config import (
    APP_NAME,
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
    COLOR_YELLOW_ACCENT,
    COLOR_YELLOW_BRIGHT,
    COLOR_YELLOW_SOFT,
    LATEST_CHROMIUM_VERSION,
    MODERN_USER_AGENT,
    USER_DATA_DIR,
    load_bookmarks,
    load_settings,
    save_bookmarks,
)
from lockdown.download_manager import DownloadManager
from lockdown.extension_manager import ExtensionManager
from lockdown.history_manager import HistoryManager
from lockdown.home_server import (
    HomeServer,
    get_downloads_url,
    get_extensions_url,
    get_settings_url,
)
from lockdown.icons import get_app_icon, get_icon
from lockdown.theme import APPLICATION_STYLESHEET
from lockdown.ui.ai_panel import LockDownAIPanel
from lockdown.ui.dialogs import (
    FlowNotesPanel,
    HistoryVaultDialog,
    ShieldFlyoutDialog,
    VPNDialog,
)
from lockdown.ui.download_flyout import LockDownDownloadFlyout
from lockdown.ui.omnibox import LockDownOmnibox
from lockdown.ui.tab_view import LockDownTabView, ensure_desktop_script_installed
from lockdown.vpn_service import VPNService
class ZenExitOverlay(QWidget):
    """Floating top-level pill overlay for leaving Zen Focus Canvas."""

    def __init__(self, main_window: "LockDownBrowserWindow"):
        super().__init__(main_window, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.main_window = main_window
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setObjectName("zenExitOverlay")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 7, 14, 7)
        layout.setSpacing(10)

        badge = QLabel("🧘 Zen Focus Canvas", self)
        badge.setStyleSheet(
            "color: #ffcf3f; font-weight: 800; font-size: 12px; background: transparent; border: none;"
        )
        layout.addWidget(badge)

        self.exit_btn = QPushButton("✕ Exit Zen (Esc)", self)
        self.exit_btn.setCursor(Qt.PointingHandCursor)
        self.exit_btn.setToolTip("Leave Zen Focus Canvas (Esc / F11)")
        self.exit_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_CORAL_PRIMARY};
                color: #ffffff;
                font-weight: 900;
                font-size: 12px;
                border-radius: 12px;
                padding: 6px 14px;
                border: 1px solid #ffcf3f;
            }}
            QPushButton:hover {{
                background: {COLOR_CORAL_HOVER};
            }}
        """)
        self.exit_btn.clicked.connect(self.main_window._exit_zen_mode)
        layout.addWidget(self.exit_btn)

        self.setStyleSheet("""
            QWidget#zenExitOverlay {
                background: rgba(24, 9, 0, 0.94);
                border: 1.5px solid rgba(255, 207, 63, 0.7);
                border-radius: 20px;
            }
        """)
        self.adjustSize()


class LockDownBrowserWindow(QMainWindow):
    def __init__(self, is_private: bool = False):
        super().__init__()
        self.is_private = is_private

        # Setup Window Title & Icon
        self.setWindowTitle(f"{APP_NAME}{' - Private Window (Zero Storage)' if is_private else ''}")
        self.setWindowIcon(get_app_icon())
        self.resize(1400, 900)

        # Core Services
        self.history_mgr = HistoryManager.get_instance()
        self.shield_stats = ShieldStats()
        self.vpn_service = VPNService(self)

        # ── WebEngine Profile — Chrome 131 desktop identity ──────────────────
        # Setting a real Chrome UA + Accept-Language makes Google / Bing / DDG
        # serve the full Chromium desktop layout (image grid, knowledge panel, etc.)
        if self.is_private:
            self.profile = QWebEngineProfile(self)   # in-memory off-the-record
        else:
            self.profile = QWebEngineProfile("lockdown", self)  # persistent named profile

        self.profile.setHttpUserAgent(MODERN_USER_AGENT)
        self.profile.setHttpAcceptLanguage("en-US,en;q=0.9")

        # Raise HTTP cache limit so images / resources are cached like Chrome
        if not self.is_private:
            self.profile.setHttpCacheMaximumSize(256 * 1024 * 1024)  # 256 MB

        self._configure_webengine_storage()

        # Attach uBlock Origin Lite request interceptor
        self.interceptor = ShieldRequestInterceptor(self.shield_stats, self)
        self.profile.setRequestInterceptor(self.interceptor)
        ensure_desktop_script_installed(self.profile)

        # Initialize Extensions engine & browse callback
        if not self.is_private:
            ExtensionManager.get_instance().initialize(self.profile)
            # Browse-folder callback is set after _init_ui so self._browse_extension_folder exists

        # Wire profile download interceptor
        self.profile.downloadRequested.connect(self._on_download_requested)

        # UI Components
        self._init_ui()
        self.apply_theme()

        # Connect browse-folder callback post UI init
        if not self.is_private:
            HomeServer.get_instance().set_browse_folder_callback(self._browse_extension_folder)

        # Connect Signals
        self.vpn_service.state_changed.connect(self._on_vpn_state_changed)
        self.shield_stats.stats_updated.connect(self._on_shields_stats_updated)
        DownloadManager.get_instance().downloads_changed.connect(self._update_download_badge)
        DownloadManager.get_instance().download_progress.connect(lambda _: self._update_download_badge())

        # Add initial home tab
        self.add_tab("lockdown://home")

    def _configure_webengine_storage(self):
        # Named profile 'lockdown' automatically manages its persistent cache & storage path safely.
        # Calling manual path overrides and synchronous clearHttpCache() locks Chromium's disk cache on Windows.
        return

    def _init_ui(self):
        # Central Tabs Container
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setElideMode(Qt.ElideRight)
        self.tabs.currentChanged.connect(self._on_current_tab_changed)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        # Tab bar corner widget cluster (+ new tab button and Zen exit button)
        corner_widget = QWidget(self.tabs)
        corner_layout = QHBoxLayout(corner_widget)
        corner_layout.setContentsMargins(0, 0, 8, 0)
        corner_layout.setSpacing(6)

        new_tab_btn = QPushButton("+", corner_widget)
        new_tab_btn.setFixedSize(32, 28)
        new_tab_btn.setCursor(Qt.PointingHandCursor)
        new_tab_btn.setToolTip("Open New Tab (Ctrl+T)")
        new_tab_btn.setStyleSheet(
            f"background: {COLOR_BLUE_BASE}; border: 1px solid {COLOR_BLUE_BORDER}; color: {COLOR_CORAL_PRIMARY}; font-size: 18px; font-weight: 700; border-radius: 6px;"
        )
        new_tab_btn.clicked.connect(lambda: self.add_tab("lockdown://home"))
        corner_layout.addWidget(new_tab_btn)

        self.zen_corner_btn = QPushButton("✕ Exit Zen (Esc)", corner_widget)
        self.zen_corner_btn.setCursor(Qt.PointingHandCursor)
        self.zen_corner_btn.setToolTip("Leave Zen Focus Canvas (Esc / F11)")
        self.zen_corner_btn.setStyleSheet(
            f"background: {COLOR_CORAL_PRIMARY}; border: 1px solid {COLOR_CORAL_HOVER}; color: #FFFFFF; font-size: 12px; font-weight: 800; border-radius: 6px; padding: 4px 10px;"
        )
        self.zen_corner_btn.clicked.connect(self._exit_zen_mode)
        self.zen_corner_btn.hide()
        corner_layout.addWidget(self.zen_corner_btn)

        self.tabs.setCornerWidget(corner_widget, Qt.TopRightCorner)

        self.setCentralWidget(self.tabs)

        self.zen_overlay = ZenExitOverlay(self)
        self.zen_overlay.hide()

        self.exit_zen_action = QAction("Exit Zen Mode", self)
        self.exit_zen_action.setShortcut("Esc")
        self.exit_zen_action.triggered.connect(self._exit_zen_mode)
        self.addAction(self.exit_zen_action)

        QApplication.instance().installEventFilter(self)

        # Sidebar Dock (Tools - closed by default on startup)
        self.sidebar = self._build_sidebar()
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sidebar)
        self.sidebar.hide()

        # AI Mode Side Panel (Dock on right)
        self.ai_panel = LockDownAIPanel(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.ai_panel)
        self.ai_panel.hide()

        # Keyboard shortcuts for AI Mode, Extensions, and Downloads
        self.ai_action = QAction("AI Mode", self)
        self.ai_action.setShortcut(QKeySequence("Ctrl+Shift+A"))
        self.ai_action.triggered.connect(self._toggle_ai_mode)
        self.addAction(self.ai_action)

        self.ext_action = QAction("Extensions", self)
        self.ext_action.setShortcut(QKeySequence("Ctrl+Shift+E"))
        self.ext_action.triggered.connect(self._open_extensions_page)
        self.addAction(self.ext_action)

        self.downloads_action = QAction("Downloads", self)
        self.downloads_action.setShortcut(QKeySequence("Ctrl+J"))
        self.downloads_action.triggered.connect(self._open_downloads_page)
        self.addAction(self.downloads_action)

        # Download Flyout popup
        self.download_flyout = LockDownDownloadFlyout(self)
        self.download_flyout.view_all_requested.connect(self._open_downloads_page)

        # Navigation Toolbar (Redesigned with Brave Omnibox & Actions)
        self.navbar = self._build_navbar()
        self.addToolBar(Qt.TopToolBarArea, self.navbar)

        # Status Bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._update_status_msg("🔒 HTTPS Secure Browser • Chrome 131 Engine Active • Shields Active")

    def _build_navbar(self) -> QToolBar:
        navbar = QToolBar("Navigation")
        navbar.setObjectName("navigationToolbar")
        navbar.setMovable(False)
        navbar.setIconSize(QSize(20, 20))

        # 1. Navigation Cluster (Left)
        self.back_action = QAction(get_icon("arrow-left.svg"), "Back (Alt+Left)", self)
        self.back_action.setShortcuts([QKeySequence.Back, QKeySequence("Alt+Left")])
        self.back_action.setEnabled(False)
        self.back_action.triggered.connect(self._go_back)
        navbar.addAction(self.back_action)

        self.fwd_action = QAction(get_icon("arrow-right.svg"), "Forward (Alt+Right)", self)
        self.fwd_action.setShortcuts([QKeySequence.Forward, QKeySequence("Alt+Right")])
        self.fwd_action.setEnabled(False)
        self.fwd_action.triggered.connect(self._go_forward)
        navbar.addAction(self.fwd_action)

        self.reload_action = QAction(get_icon("refresh.svg"), "Reload (Ctrl+R / F5)", self)
        self.reload_action.setShortcuts([QKeySequence.Refresh, QKeySequence("F5")])
        self.reload_action.triggered.connect(self._reload_or_stop_current_tab)
        navbar.addAction(self.reload_action)

        home_action = QAction(get_icon("home.svg"), "Home", self)
        home_action.setShortcut("Alt+Home")
        home_action.triggered.connect(lambda: self.navigate_url("lockdown://home"))
        navbar.addAction(home_action)

        # 2. Brave-Style Integrated Omnibox (Center Stretch)
        self.omnibox = LockDownOmnibox(self)
        self.omnibox.return_pressed.connect(self._on_address_entered)
        self.omnibox.shield_clicked.connect(self._open_shields_dialog)
        self.omnibox.bookmark_clicked.connect(self._toggle_bookmark_current_page)
        navbar.addWidget(self.omnibox)

        # 3. Right Action Cluster
        # Proton VPN Pill
        self.vpn_pill = QPushButton("🛡️ VPN OFF")
        self.vpn_pill.setCursor(Qt.PointingHandCursor)
        self.vpn_pill.setToolTip("Proton-inspired Secure VPN Tunnel")
        self.vpn_pill.setStyleSheet(
            f"background: {COLOR_BLUE_BASE}; border: 1.5px solid {COLOR_BLUE_BORDER}; color: {COLOR_CORAL_PRIMARY}; font-weight: 700; font-size: 11.5px; border-radius: 14px; padding: 5px 12px;"
        )
        self.vpn_pill.clicked.connect(self._open_vpn_dialog)
        navbar.addWidget(self.vpn_pill)

        # Extensions Hub Button
        self.ext_pill = QPushButton("🧩 Extensions")
        self.ext_pill.setCursor(Qt.PointingHandCursor)
        self.ext_pill.setToolTip("Extensions Manager & Library (Ctrl+Shift+E)")
        self.ext_pill.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_BLUE_BASE};
                border: 1.5px solid {COLOR_BLUE_BORDER};
                color: {COLOR_CORAL_PRIMARY};
                font-weight: 700;
                font-size: 11.5px;
                border-radius: 14px;
                padding: 5px 12px;
            }}
            QPushButton:hover {{
                background: {COLOR_YELLOW_SOFT};
                border-color: {COLOR_CORAL_PRIMARY};
            }}
        """)
        self.ext_pill.clicked.connect(self._open_extensions_page)
        navbar.addWidget(self.ext_pill)

        # Gemini AI Mode Button
        self.ai_pill = QPushButton("✨ AI Mode")
        self.ai_pill.setCursor(Qt.PointingHandCursor)
        self.ai_pill.setToolTip("Gemini Multimodal Browser Assistant (Ctrl+Shift+A)")
        self.ai_pill.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_YELLOW_BRIGHT};
                border: 1.5px solid {COLOR_YELLOW_ACCENT};
                color: {COLOR_IVORY_LIGHT};
                font-weight: 800;
                font-size: 11.5px;
                border-radius: 14px;
                padding: 5px 12px;
            }}
            QPushButton:hover {{
                background: {COLOR_CORAL_PRIMARY};
                color: #FFFFFF;
                border-color: {COLOR_CORAL_PRIMARY};
            }}
        """)
        self.ai_pill.clicked.connect(self._toggle_ai_mode)
        navbar.addWidget(self.ai_pill)

        # Downloads Button (with dynamic counter badge & interactive popup)
        self.download_btn = QPushButton("📥")
        self.download_btn.setCursor(Qt.PointingHandCursor)
        self.download_btn.setToolTip("Downloads Manager & Flyout (Ctrl+J)")
        self.download_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_BLUE_BASE};
                border: 1.5px solid {COLOR_BLUE_BORDER};
                color: {COLOR_CORAL_PRIMARY};
                font-weight: 700;
                font-size: 12px;
                border-radius: 14px;
                padding: 5px 10px;
            }}
            QPushButton:hover {{
                background: {COLOR_YELLOW_SOFT};
                border-color: {COLOR_CORAL_PRIMARY};
            }}
        """)
        self.download_btn.clicked.connect(self._toggle_download_flyout)
        navbar.addWidget(self.download_btn)

        # Zen Focus Mode Button
        self.zen_action = QAction(get_icon("zen.svg"), "Zen Mode", self)
        self.zen_action.setToolTip("Toggle Zen Focus Canvas (F11)")
        self.zen_action.setCheckable(True)
        self.zen_action.setShortcut("F11")
        self.zen_action.triggered.connect(self._toggle_zen_mode)
        navbar.addAction(self.zen_action)

        # Snapshot Camera Tool
        snap_action = QAction(get_icon("camera.svg"), "Snapshot", self)
        snap_action.setToolTip("Capture Snapshot of Current Page")
        snap_action.triggered.connect(lambda: self.current_browser() and self.current_browser().take_snapshot())
        navbar.addAction(snap_action)

        # Toggle Sidebar Dock
        side_toggle_action = QAction(get_icon("sidebar.svg"), "Sidebar", self)
        side_toggle_action.setToolTip("Toggle Tools Sidebar")
        side_toggle_action.triggered.connect(lambda: self.sidebar.setVisible(not self.sidebar.isVisible()))
        navbar.addAction(side_toggle_action)

        # Settings
        settings_action = QAction(get_icon("settings.svg"), "Settings", self)
        settings_action.setToolTip("Browser Settings & Encrypted Vault")
        settings_action.triggered.connect(self._open_settings_dialog)
        navbar.addAction(settings_action)

        return navbar

    def _build_sidebar(self) -> QDockWidget:
        dock = QDockWidget("Tools", self)
        dock.setObjectName("sidebarDock")
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable)

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 14, 12, 14)
        layout.setSpacing(12)

        # Brand header with Samurai logo
        brand_row = QHBoxLayout()
        logo_lbl = QLabel()
        logo_lbl.setPixmap(get_app_icon().pixmap(32, 32))
        brand_row.addWidget(logo_lbl)

        brand_text = QLabel("LOCK DOWN")
        brand_text.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {COLOR_IVORY_LIGHT}; letter-spacing: 1.5px;")
        brand_row.addWidget(brand_text)
        brand_row.addStretch()
        layout.addLayout(brand_row)

        if self.is_private:
            p_badge = QLabel("🕶️ ZERO-STORAGE PRIVATE")
            p_badge.setStyleSheet(f"background: {COLOR_CORAL_PRIMARY}; color: #FFFFFF; font-size: 10px; font-weight: 800; padding: 4px; border-radius: 4px; text-align: center;")
            p_badge.setAlignment(Qt.AlignCenter)
            layout.addWidget(p_badge)

        # Opera Flow / Quick Notes Scratchpad
        self.flow_notes = FlowNotesPanel(self)
        layout.addWidget(self.flow_notes, 1)

        # Security & Vault
        tools_label = QLabel("SECURITY & VAULT")
        tools_label.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {COLOR_IVORY_MUTED}; letter-spacing: 1px;")
        layout.addWidget(tools_label)

        vault_btn = QPushButton("🔒 Encrypted History Vault")
        vault_btn.clicked.connect(self._open_history_vault)
        layout.addWidget(vault_btn)

        priv_btn = QPushButton("🕶️ New Private Window")
        priv_btn.clicked.connect(self._open_private_window)
        layout.addWidget(priv_btn)

        # Intelligence, Extensions & Downloads
        intel_label = QLabel("INTELLIGENCE, EXTENSIONS & FILES")
        intel_label.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {COLOR_IVORY_MUTED}; letter-spacing: 1px;")
        layout.addWidget(intel_label)

        sidebar_ai_btn = QPushButton("✨ Gemini AI Assistant (Ctrl+Shift+A)")
        sidebar_ai_btn.clicked.connect(self._toggle_ai_mode)
        layout.addWidget(sidebar_ai_btn)

        sidebar_ext_btn = QPushButton("🧩 Extensions Hub & Store")
        sidebar_ext_btn.clicked.connect(self._open_extensions_page)
        layout.addWidget(sidebar_ext_btn)

        sidebar_dl_btn = QPushButton("📥 Downloads Manager (Ctrl+J)")
        sidebar_dl_btn.clicked.connect(self._open_downloads_page)
        layout.addWidget(sidebar_dl_btn)

        dock.setWidget(panel)
        return dock

    def add_tab(
        self,
        url: str = "lockdown://home",
        label: str = "New Tab",
        background: bool = False,
    ) -> LockDownTabView:
        tab_view = LockDownTabView(
            browser_window=self,
            profile=self.profile,
            url=url,
            is_private=self.is_private,
        )

        index = self.tabs.addTab(tab_view, get_icon("home.svg"), label)
        self.tabs.setTabToolTip(index, url)

        # Hook signals
        tab_view.custom_url_changed.connect(lambda qurl, view=tab_view: self._update_urlbar_if_active(qurl, view))
        tab_view.custom_title_changed.connect(lambda title, view=tab_view: self._update_tab_title(title, view))
        tab_view.custom_icon_changed.connect(lambda icon, view=tab_view: self._update_tab_icon(icon, view))
        tab_view.loadProgress.connect(self._update_progress)
        tab_view.urlChanged.connect(lambda _, view=tab_view: self._refresh_nav_buttons(view))
        tab_view.loadFinished.connect(lambda _, view=tab_view: self._refresh_nav_buttons(view))
        tab_view.loadStarted.connect(lambda view=tab_view: self._refresh_nav_buttons(view))

        if not background:
            self.tabs.setCurrentIndex(index)
            self._refresh_nav_buttons(tab_view)

        return tab_view

    def close_tab(self, index: int):
        if self.tabs.count() <= 1:
            self.current_browser().navigate("lockdown://home")
            return

        widget = self.tabs.widget(index)
        self.tabs.removeTab(index)
        widget.deleteLater()
        self._refresh_nav_buttons()

    def current_browser(self) -> Optional[LockDownTabView]:
        widget = self.tabs.currentWidget()
        if isinstance(widget, LockDownTabView):
            return widget
        return None

    current_tab = current_browser

    def navigate_url(self, url: str):
        b = self.current_browser()
        if b:
            b.navigate(url)

    def _go_back(self):
        b = self.current_browser()
        if b:
            b.triggerPageAction(QWebEnginePage.Back)
            self._refresh_nav_buttons(b)

    def _go_forward(self):
        b = self.current_browser()
        if b:
            b.triggerPageAction(QWebEnginePage.Forward)
            self._refresh_nav_buttons(b)

    def _reload_or_stop_current_tab(self):
        b = self.current_browser()
        if not b:
            return

        url_str = b.url().toString()
        if self._is_home_url(url_str):
            b.navigate("lockdown://home")
        else:
            b.triggerPageAction(QWebEnginePage.Reload)
        self._refresh_nav_buttons(b)

    def _refresh_nav_buttons(self, view=None):
        b = self.current_browser()
        if not b:
            self.back_action.setEnabled(False)
            self.fwd_action.setEnabled(False)
            return
        if view is not None and view != b:
            return
        self.back_action.setEnabled(b.history().canGoBack())
        self.fwd_action.setEnabled(b.history().canGoForward())

    def _on_address_entered(self):
        text = self.omnibox.text().strip()
        if text:
            self.navigate_url(text)

    def _update_urlbar_if_active(self, qurl: QUrl, view: LockDownTabView):
        if view == self.current_browser():
            url_str = qurl.toString()
            if self._is_home_url(url_str):
                self.omnibox.setText("lockdown://home")
            elif self._is_extensions_url(url_str):
                self.omnibox.setText("lockdown://extensions")
            elif self._is_settings_url(url_str):
                self.omnibox.setText("lockdown://settings")
            elif self._is_downloads_url(url_str):
                self.omnibox.setText("lockdown://downloads")
            else:
                self.omnibox.setText(url_str)
            self.omnibox.setCursorPosition(0)

            # Update security status and shield count
            self.omnibox.update_security_status(url_str)
            domain = urlparse(url_str).netloc
            count = self.shield_stats.get_count_for_host(domain)
            self.omnibox.update_shield_count(count)

            # Check bookmark status
            bms = load_bookmarks()
            is_bm = any(b.get("url") == url_str for b in bms)
            self.omnibox.set_bookmarked(is_bm)

    def _update_tab_title(self, title: str, view: LockDownTabView):
        index = self.tabs.indexOf(view)
        if index != -1:
            short = title[:24] + "..." if len(title) > 24 else title
            self.tabs.setTabText(index, short)
            self.tabs.setTabToolTip(index, title)
            if view == self.current_browser():
                self.setWindowTitle(f"{title} - {APP_NAME}{' (Private)' if self.is_private else ''}")

    def _update_tab_icon(self, icon: QIcon, view: LockDownTabView):
        index = self.tabs.indexOf(view)
        if index != -1 and not icon.isNull():
            self.tabs.setTabIcon(index, icon)

    def _update_progress(self, progress: int):
        if progress < 100:
            self._update_status_msg(f"⏳ Loading... {progress}%")
        else:
            b = self.current_browser()
            if b:
                scheme = b.url().scheme().lower()
                host   = b.url().host().lower()
                if scheme == "https":
                    self._update_status_msg("🔒 HTTPS — Secure & Encrypted  •  Shields Active")
                elif scheme == "http" and host in ("localhost", "127.0.0.1", "::1"):
                    self._update_status_msg("🏠 Local page (HTTP — internal only)")
                else:
                    self._update_status_msg("⚠️  Insecure Connection (HTTP) — data may be visible to others")
            else:
                self._update_status_msg("🔒 HTTPS Secure Browser  •  Shields Active")

    def _update_status_msg(self, msg: str):
        vpn_info = f"🛡 VPN: {self.vpn_service.current_server['flag']}" if self.vpn_service.is_connected else "VPN: Off"
        self.status.showMessage(f"{msg}  |  {vpn_info}")

    def _on_current_tab_changed(self, index: int):
        b = self.current_browser()
        if b:
            self._update_urlbar_if_active(b.url(), b)
            self.setWindowTitle(f"{b.current_title} - {APP_NAME}{' (Private)' if self.is_private else ''}")
            self._refresh_nav_buttons(b)
            if hasattr(self, "ai_panel") and self.ai_panel.isVisible():
                self.ai_panel.capture_current_tab()
        else:
            self._refresh_nav_buttons()

    def _on_shields_stats_updated(self):
        b = self.current_browser()
        if b:
            domain = urlparse(b.url().toString()).netloc
            count = self.shield_stats.get_count_for_host(domain)
            self.omnibox.update_shield_count(count)

    def _open_shields_dialog(self):
        b = self.current_browser()
        current_url = b.url().toString() if b else "lockdown://home"
        dlg = ShieldFlyoutDialog(self.shield_stats, current_url, self)
        pos = self.navbar.mapToGlobal(QPoint(self.navbar.width() - 420, self.navbar.height()))
        dlg.move(pos)
        dlg.exec_()

    def _open_vpn_dialog(self):
        dlg = VPNDialog(self.vpn_service, self)
        dlg.exec_()

    def _on_vpn_state_changed(self, is_connected: bool, server_name: str):
        if is_connected:
            srv = self.vpn_service.current_server
            self.vpn_pill.setText(f"{srv['flag']} PROTECTED")
            self.vpn_pill.setStyleSheet(
                f"background: rgba(78, 204, 163, 0.2); border: 1.5px solid #4ECCA3; color: #4ECCA3; font-weight: 800; font-size: 11.5px; border-radius: 14px; padding: 5px 12px;"
            )
        else:
            self.vpn_pill.setText("🛡️ VPN OFF")
            self.vpn_pill.setStyleSheet(
                f"background: {COLOR_BLUE_BASE}; border: 1.5px solid {COLOR_BLUE_BORDER}; color: {COLOR_CORAL_PRIMARY}; font-weight: 700; font-size: 11.5px; border-radius: 14px; padding: 5px 12px;"
            )
        self._update_status_msg("VPN state updated")

    def _open_history_vault(self):
        dlg = HistoryVaultDialog(self)
        dlg.exec_()

    def _open_settings_dialog(self):
        """Open the dedicated Settings page in a new or existing tab."""
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if hasattr(w, "url") and self._is_settings_url(w.url().toString()):
                self.tabs.setCurrentIndex(i)
                return
        self.add_tab("lockdown://settings", "Settings")

    def _open_private_window(self):
        if not hasattr(self, "_child_windows"):
            self._child_windows = []
        priv_win = LockDownBrowserWindow(is_private=True)
        self._child_windows.append(priv_win)
        priv_win.show()

    def _open_extensions_page(self):
        """Open the Extensions Hub in a new or existing tab."""
        # Check if already open
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if hasattr(w, "url") and self._is_extensions_url(w.url().toString()):
                self.tabs.setCurrentIndex(i)
                return
        self.add_tab("lockdown://extensions", "Extensions")

    def _open_downloads_page(self):
        """Open the dedicated Downloads page in a new or existing tab."""
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if hasattr(w, "url") and self._is_downloads_url(w.url().toString()):
                self.tabs.setCurrentIndex(i)
                return
        self.add_tab("lockdown://downloads", "Downloads")

    def _toggle_download_flyout(self):
        """Toggle the floating downloads flyout anchored below the download button."""
        if not hasattr(self, "download_flyout"):
            return
        if self.download_flyout.isVisible():
            self.download_flyout.hide()
        else:
            self.download_flyout.show_anchored(self.download_btn)

    def _on_download_requested(self, download):
        """Called automatically when any tab initiates a file download."""
        item = DownloadManager.get_instance().handle_download_request(download)
        self._update_download_badge()
        # Pop out the download flyout so the user immediately sees the file downloading!
        if hasattr(self, "download_flyout") and hasattr(self, "download_btn"):
            self.download_flyout.show_anchored(self.download_btn)

    def _update_download_badge(self):
        """Update download button badge counter & appearance based on active transfers."""
        if not hasattr(self, "download_btn"):
            return
        active_count = DownloadManager.get_instance().get_active_count()
        if active_count > 0:
            self.download_btn.setText(f"📥 {active_count}")
            self.download_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLOR_CORAL_PRIMARY};
                    border: 1.5px solid {COLOR_CORAL_HOVER};
                    color: #FFFFFF;
                    font-weight: 800;
                    font-size: 11.5px;
                    border-radius: 14px;
                    padding: 5px 12px;
                }}
                QPushButton:hover {{
                    background: {COLOR_CORAL_HOVER};
                }}
            """)
        else:
            self.download_btn.setText("📥")
            self.download_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLOR_BLUE_BASE};
                    border: 1.5px solid {COLOR_BLUE_BORDER};
                    color: {COLOR_CORAL_PRIMARY};
                    font-weight: 700;
                    font-size: 12px;
                    border-radius: 14px;
                    padding: 5px 10px;
                }}
                QPushButton:hover {{
                    background: {COLOR_YELLOW_SOFT};
                    border-color: {COLOR_CORAL_PRIMARY};
                }}
            """)

    def _toggle_ai_mode(self):
        """Toggle the Gemini AI Mode side panel."""
        if not hasattr(self, "ai_panel"):
            return
        if self.ai_panel.isVisible():
            self.ai_panel.hide()
            self.ai_pill.setText("✨ AI Mode")
            self.ai_pill.setStyleSheet(f"""
                QPushButton {{
                    background: {COLOR_YELLOW_BRIGHT};
                    border: 1.5px solid {COLOR_YELLOW_ACCENT};
                    color: {COLOR_IVORY_LIGHT};
                    font-weight: 800;
                    font-size: 11.5px;
                    border-radius: 14px;
                    padding: 5px 12px;
                }}
                QPushButton:hover {{
                    background: {COLOR_CORAL_PRIMARY};
                    color: #FFFFFF;
                    border-color: {COLOR_CORAL_PRIMARY};
                }}
            """)
        else:
            self.ai_panel.show()
            self.ai_panel.capture_current_tab()
            self.ai_pill.setText("✨ AI Mode ●")
            self.ai_pill.setStyleSheet(f"""
                QPushButton {{
                    background: {COLOR_CORAL_PRIMARY};
                    border: 1.5px solid {COLOR_CORAL_HOVER};
                    color: #FFFFFF;
                    font-weight: 800;
                    font-size: 11.5px;
                    border-radius: 14px;
                    padding: 5px 12px;
                }}
                QPushButton:hover {{
                    background: {COLOR_CORAL_HOVER};
                }}
            """)
        self._update_status_msg("🤖 AI Mode Active  •  Gemini Vision Ready" if self.ai_panel.isVisible() else "🔒 HTTPS Secure Browser  •  Shields Active")

    def _browse_extension_folder(self):
        """Opens a native folder picker for loading an unpacked extension. Called from Flask route."""
        from lockdown.qt_compat import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "Select Unpacked Extension Folder", str(self.profile.persistentStoragePath() if hasattr(self.profile, 'persistentStoragePath') else ""))
        return folder if folder else None

    @property
    def is_zen_mode(self) -> bool:
        return hasattr(self, "zen_action") and self.zen_action.isChecked()

    def _toggle_zen_mode(self, checked: bool):
        self.sidebar.setVisible(not checked)
        self.navbar.setVisible(not checked)
        self.status.setVisible(not checked)
        if hasattr(self, "ai_panel") and checked:
            self.ai_panel.setVisible(False)
        if hasattr(self, "zen_corner_btn"):
            self.zen_corner_btn.setVisible(checked)
        if checked:
            self.showFullScreen()
            if hasattr(self, "zen_overlay"):
                self.zen_overlay.show()
                self._position_zen_overlay()
            self._update_status_msg("Zen Mode: Press Esc or click 'Exit Zen' to restore controls")
        else:
            if hasattr(self, "zen_overlay"):
                self.zen_overlay.hide()
            self.showMaximized()

    def _exit_zen_mode(self):
        if hasattr(self, "zen_action") and self.zen_action.isChecked():
            self.zen_action.setChecked(False)
            self._toggle_zen_mode(False)

    def _position_zen_overlay(self):
        if not hasattr(self, "zen_overlay"):
            return
        self.zen_overlay.adjustSize()
        top_left = self.mapToGlobal(QPoint(0, 0))
        x = top_left.x() + max(0, self.width() - self.zen_overlay.width() - 24)
        y = top_left.y() + 18
        self.zen_overlay.move(x, y)
        self.zen_overlay.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.is_zen_mode:
            self._position_zen_overlay()

    def moveEvent(self, event):
        super().moveEvent(event)
        if self.is_zen_mode:
            self._position_zen_overlay()

    def changeEvent(self, event):
        super().changeEvent(event)
        if self.is_zen_mode and hasattr(self, "zen_overlay"):
            self._position_zen_overlay()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and self.is_zen_mode:
            if event.key() in (Qt.Key_Escape, Qt.Key_F11):
                self._exit_zen_mode()
                return True
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        if hasattr(self, "zen_overlay"):
            self.zen_overlay.close()
        super().closeEvent(event)

    def _toggle_bookmark_current_page(self):
        b = self.current_browser()
        if not b:
            return
        url = b.url().toString()
        title = b.current_title
        bms = load_bookmarks()
        existing = [bm for bm in bms if bm.get("url") == url]
        if existing:
            bms = [bm for bm in bms if bm.get("url") != url]
            save_bookmarks(bms)
            self.omnibox.set_bookmarked(False)
            QMessageBox.information(self, "Bookmark Removed", f"Removed bookmark for {title}")
        else:
            bms.append({"title": title, "url": url, "folder": "Default"})
            save_bookmarks(bms)
            self.omnibox.set_bookmarked(True)
            QMessageBox.information(self, "Bookmark Added", f"Saved '{title}' to bookmarks.")

    def apply_theme(self):
        self.setStyleSheet(APPLICATION_STYLESHEET)

    @staticmethod
    def _is_home_url(url_str: str) -> bool:
        return (
            "home.html" in url_str
            or "home_live_" in url_str
            or ("127.0.0.1:" in url_str and "/lockdown-home" in url_str)
        )

    @staticmethod
    def _is_extensions_url(url_str: str) -> bool:
        return "127.0.0.1:" in url_str and "/lockdown-extensions" in url_str

    @staticmethod
    def _is_settings_url(url_str: str) -> bool:
        return "127.0.0.1:" in url_str and "/lockdown-settings" in url_str

    @staticmethod
    def _is_downloads_url(url_str: str) -> bool:
        return "127.0.0.1:" in url_str and "/lockdown-downloads" in url_str
