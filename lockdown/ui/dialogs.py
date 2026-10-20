"""Lock Down UI Dialogs and Panels.
Includes uBlock Origin Lite Shield Flyout, Proton VPN Controller,
AES-256-GCM Encrypted History Vault, Settings, and Flow Notes Panel.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from lockdown.qt_compat import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFont,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QIcon,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSize,
    QSizePolicy,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QTimer,
    QVBoxLayout,
    QWidget,
    Qt,
    pyqtSignal,
)

from lockdown.blocker import ShieldStats
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
    DEFAULT_WORKSPACES,
    SEARCH_ENGINES,
    VAULT_DIR,
    load_bookmarks,
    load_flow_notes,
    load_settings,
    save_bookmarks,
    save_flow_notes,
    save_settings,
)
from lockdown.crypto_vault import CryptoVault
from lockdown.drive_sync import GoogleDriveSync
from lockdown.history_manager import HistoryManager
from lockdown.icons import get_app_icon, get_icon
from lockdown.vpn_service import PROTON_SERVERS, VPNService


class ShieldFlyoutDialog(QDialog):
    """uBlock Origin Lite inspired Shield popup with per-site telemetry and toggle controls."""

    def __init__(self, stats: ShieldStats, current_url: str, parent=None):
        super().__init__(parent)
        self.stats = stats
        self.current_url = current_url
        self.domain = urlparse(current_url).netloc or "Current Page"

        self.setWindowTitle(f"Lock Down Shields - {self.domain}")
        self.setWindowIcon(get_icon("shield.svg"))
        self.setFixedSize(380, 480)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # Header with Logo & Domain
        header = QHBoxLayout()
        shield_icon = QLabel()
        shield_icon.setPixmap(get_icon("shield.svg").pixmap(28, 28))
        header.addWidget(shield_icon)

        title_box = QVBoxLayout()
        title = QLabel("LOCK DOWN SHIELDS")
        title.setStyleSheet(f"font-size: 13px; font-weight: 800; color: {COLOR_CORAL_PRIMARY}; letter-spacing: 1px;")
        domain_lbl = QLabel(self.domain)
        domain_lbl.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {COLOR_IVORY_LIGHT};")
        title_box.addWidget(title)
        title_box.addWidget(domain_lbl)
        header.addLayout(title_box)
        header.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(f"background: transparent; border: none; font-size: 16px; color: {COLOR_IVORY_MUTED};")
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        # Master Power Toggle (Brave style)
        power_card = QFrame()
        power_card.setStyleSheet(f"background: {COLOR_BLUE_BASE}; border-radius: 12px; border: 1px solid {COLOR_BLUE_BORDER};")
        power_box = QHBoxLayout(power_card)
        power_box.setContentsMargins(10, 10, 10, 10)

        settings = load_settings()
        self.is_whitelisted = self.stats.is_whitelisted(self.domain)
        is_active = settings.get("shields_enabled", True) and not self.is_whitelisted

        self.power_label = QLabel("Protection Active" if is_active else "Protection Paused")
        self.power_label.setStyleSheet(f"font-weight: 700; font-size: 14px; color: {COLOR_IVORY_LIGHT};")
        power_box.addWidget(self.power_label)
        power_box.addStretch()

        self.power_btn = QPushButton("Shield ON" if is_active else "Shield OFF")
        self.power_btn.setCheckable(True)
        self.power_btn.setChecked(is_active)
        self.power_btn.setStyleSheet(
            f"background: {COLOR_CORAL_PRIMARY if is_active else COLOR_BLUE_SURFACE}; color: #FFFFFF; font-weight: 700; border-radius: 14px; padding: 6px 14px;"
        )
        self.power_btn.clicked.connect(self._toggle_power)
        power_box.addWidget(self.power_btn)
        layout.addWidget(power_card)

        # Telemetry Metrics Grid
        metrics = QFrame()
        metrics.setStyleSheet(f"background: {COLOR_BLUE_BASE}; border-radius: 12px; border: 1px solid {COLOR_BLUE_BORDER};")
        m_layout = QFormLayout(metrics)
        m_layout.setContentsMargins(14, 12, 14, 12)
        m_layout.setSpacing(10)

        site_count = self.stats.get_count_for_host(self.domain)
        self.lbl_site_blocked = QLabel(str(site_count))
        self.lbl_site_blocked.setStyleSheet(f"font-weight: 800; font-size: 14px; color: {COLOR_CORAL_PRIMARY};")
        m_layout.addRow("Blocked on this page:", self.lbl_site_blocked)

        lbl_total_ads = QLabel(f"{self.stats.ads_blocked_total:,}")
        lbl_total_ads.setStyleSheet(f"font-weight: 700; color: {COLOR_IVORY_LIGHT};")
        m_layout.addRow("Total Ads Blocked:", lbl_total_ads)

        lbl_total_trackers = QLabel(f"{self.stats.trackers_blocked_total:,}")
        lbl_total_trackers.setStyleSheet(f"font-weight: 700; color: {COLOR_IVORY_LIGHT};")
        m_layout.addRow("Trackers & Beacons:", lbl_total_trackers)

        lbl_cookies = QLabel(f"{self.stats.cookies_blocked_total:,}")
        lbl_cookies.setStyleSheet(f"font-weight: 700; color: {COLOR_IVORY_LIGHT};")
        m_layout.addRow("Cookie Notices Filtered:", lbl_cookies)
        layout.addWidget(metrics)

        # uBlock Origin Lite Granular Toggles
        toggles_box = QVBoxLayout()
        toggles_box.setSpacing(8)

        self.cb_ads = QCheckBox("Block Advertisements & Popups (uBlock Lite)")
        self.cb_ads.setChecked(settings.get("ad_blocking", True))
        self.cb_ads.stateChanged.connect(self._save_toggles)
        toggles_box.addWidget(self.cb_ads)

        self.cb_trackers = QCheckBox("Block Cross-Site Trackers & Telemetry")
        self.cb_trackers.setChecked(settings.get("tracker_blocking", True))
        self.cb_trackers.stateChanged.connect(self._save_toggles)
        toggles_box.addWidget(self.cb_trackers)

        self.cb_cookies = QCheckBox("Auto-Hide Cookie Consent Banners")
        self.cb_cookies.setChecked(settings.get("cookie_banner_blocking", True))
        self.cb_cookies.stateChanged.connect(self._save_toggles)
        toggles_box.addWidget(self.cb_cookies)

        self.cb_https = QCheckBox("Enforce Strict HTTPS Upgrade")
        self.cb_https.setChecked(settings.get("https_upgrade", True))
        self.cb_https.stateChanged.connect(self._save_toggles)
        toggles_box.addWidget(self.cb_https)

        layout.addLayout(toggles_box)

        # Whitelist button
        self.whitelist_btn = QPushButton("Whitelist This Site (Disable on site)" if not self.is_whitelisted else "Remove from Whitelist")
        self.whitelist_btn.setStyleSheet(f"background: {COLOR_BLUE_SURFACE}; color: {COLOR_IVORY_LIGHT}; border: 1px solid {COLOR_BLUE_BORDER}; padding: 8px;")
        self.whitelist_btn.clicked.connect(self._toggle_whitelist)
        layout.addWidget(self.whitelist_btn)

    def _toggle_power(self, checked):
        settings = load_settings()
        settings["shields_enabled"] = checked
        save_settings(settings)
        self.power_label.setText("Protection Active" if checked else "Protection Paused")
        self.power_btn.setText("Shield ON" if checked else "Shield OFF")
        self.power_btn.setStyleSheet(
            f"background: {COLOR_CORAL_PRIMARY if checked else COLOR_BLUE_SURFACE}; color: #FFFFFF; font-weight: 700; border-radius: 14px; padding: 6px 14px;"
        )

    def _save_toggles(self):
        settings = load_settings()
        settings["ad_blocking"] = self.cb_ads.isChecked()
        settings["tracker_blocking"] = self.cb_trackers.isChecked()
        settings["cookie_banner_blocking"] = self.cb_cookies.isChecked()
        settings["https_upgrade"] = self.cb_https.isChecked()
        save_settings(settings)

    def _toggle_whitelist(self):
        whitelisted = self.stats.toggle_whitelist(self.domain)
        self.is_whitelisted = whitelisted
        self.whitelist_btn.setText("Remove from Whitelist" if whitelisted else "Whitelist This Site (Disable on site)")
        self.power_label.setText("Protection Paused (Whitelisted)" if whitelisted else "Protection Active")


class VPNDialog(QDialog):
    """Proton VPN-inspired secure connection manager."""

    def __init__(self, vpn_service: VPNService, parent=None):
        super().__init__(parent)
        self.vpn = vpn_service
        self.setWindowTitle("Lock Down VPN - Proton Secure Service")
        self.setWindowIcon(get_icon("vpn.svg"))
        self.setFixedSize(480, 560)
        self.setStyleSheet(f"background-color: {COLOR_BLUE_DARK}; color: {COLOR_IVORY_LIGHT};")

        self._build_ui()
        self.vpn.stats_updated.connect(self._on_stats_updated)
        self.vpn.state_changed.connect(self._on_state_changed)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(get_icon("vpn.svg").pixmap(32, 32))
        hdr.addWidget(icon)

        titles = QVBoxLayout()
        main_title = QLabel("PROTON SECURE TUNNEL")
        main_title.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {COLOR_CORAL_PRIMARY}; letter-spacing: 1.5px;")
        sub_title = QLabel("Zero-Logging Encrypted Proxy Architecture")
        sub_title.setStyleSheet(f"font-size: 11px; color: {COLOR_IVORY_MUTED};")
        titles.addWidget(main_title)
        titles.addWidget(sub_title)
        hdr.addLayout(titles)
        hdr.addStretch()
        layout.addLayout(hdr)

        # Status & Quick Connect Card
        status_card = QFrame()
        status_card.setStyleSheet(f"background: {COLOR_BLUE_BASE}; border-radius: 14px; border: 1.5px solid {COLOR_BLUE_BORDER}; padding: 12px;")
        s_layout = QVBoxLayout(status_card)
        s_layout.setSpacing(10)

        top_s = QHBoxLayout()
        self.status_badge = QLabel("🟢 PROTECTED" if self.vpn.is_connected else "🔴 DISCONNECTED")
        self.status_badge.setStyleSheet(
            f"font-weight: 800; font-size: 13px; color: {'#4ECCA3' if self.vpn.is_connected else '#FF4A4A'};"
        )
        top_s.addWidget(self.status_badge)
        top_s.addStretch()

        self.timer_label = QLabel("00:00:00" if self.vpn.is_connected else "--:--:--")
        self.timer_label.setStyleSheet(f"font-weight: 600; font-size: 13px; color: {COLOR_IVORY_MUTED};")
        top_s.addWidget(self.timer_label)
        s_layout.addLayout(top_s)

        # Connection metrics
        info_row = QHBoxLayout()
        self.ip_lbl = QLabel(f"IP: {self.vpn.current_server['ip'] if self.vpn.is_connected else 'ISP Masked'}")
        self.ip_lbl.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {COLOR_IVORY_LIGHT};")
        info_row.addWidget(self.ip_lbl)

        info_row.addStretch()
        self.ping_lbl = QLabel(f"Ping: {self.vpn.current_server['ping']} ms")
        self.ping_lbl.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {COLOR_CORAL_PRIMARY};")
        info_row.addWidget(self.ping_lbl)
        s_layout.addLayout(info_row)

        self.connect_btn = QPushButton("DISCONNECT" if self.vpn.is_connected else "QUICK CONNECT")
        self.connect_btn.setStyleSheet(
            f"background: {COLOR_CORAL_PRIMARY}; color: #FFFFFF; font-weight: 800; font-size: 14px; padding: 10px; border-radius: 8px;"
        )
        self.connect_btn.clicked.connect(self._toggle_connection)
        s_layout.addWidget(self.connect_btn)
        layout.addWidget(status_card)

        # Server Locations List
        loc_label = QLabel("SECURE CORE & FAST SERVERS")
        loc_label.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {COLOR_IVORY_MUTED}; letter-spacing: 1px;")
        layout.addWidget(loc_label)

        self.server_list = QListWidget()
        for s in PROTON_SERVERS:
            item = QListWidgetItem(f"{s['flag']}  {s['name']}  •  {s['tier']}  ({s['ping']}ms)")
            item.setData(Qt.UserRole, s["id"])
            if s["id"] == self.vpn.current_server["id"]:
                item.setSelected(True)
            self.server_list.addItem(item)
        self.server_list.itemClicked.connect(self._on_server_selected)
        layout.addWidget(self.server_list, 1)

        # Settings: Protocol & Kill Switch
        bottom_box = QHBoxLayout()
        proto_lbl = QLabel("Protocol:")
        proto_lbl.setStyleSheet(f"color: {COLOR_IVORY_MUTED}; font-size: 12px;")
        bottom_box.addWidget(proto_lbl)

        self.proto_combo = QComboBox()
        self.proto_combo.addItems(["WireGuard (Fastest)", "Stealth (Anti-DPI)", "OpenVPN (TCP)"])
        self.proto_combo.setCurrentText(self.vpn.protocol)
        self.proto_combo.currentTextChanged.connect(self._on_proto_changed)
        bottom_box.addWidget(self.proto_combo)
        bottom_box.addStretch()

        self.cb_kill = QCheckBox("Kill Switch")
        self.cb_kill.setChecked(self.vpn.kill_switch)
        self.cb_kill.stateChanged.connect(lambda state: self.vpn.set_kill_switch(state == Qt.Checked))
        bottom_box.addWidget(self.cb_kill)
        layout.addLayout(bottom_box)

    def _toggle_connection(self):
        if self.vpn.is_connected:
            self.vpn.disconnect_vpn()
        else:
            self.vpn.connect_vpn()

    def _on_state_changed(self, connected: bool, server_name: str):
        self.connect_btn.setText("DISCONNECT" if connected else "QUICK CONNECT")
        self.status_badge.setText("🟢 PROTECTED" if connected else "🔴 DISCONNECTED")
        self.status_badge.setStyleSheet(
            f"font-weight: 800; font-size: 13px; color: {'#4ECCA3' if connected else '#FF4A4A'};"
        )
        if not connected:
            self.timer_label.setText("--:--:--")
            self.ip_lbl.setText("IP: ISP Standard")

    def _on_stats_updated(self, stats: dict):
        self.timer_label.setText(stats.get("duration", "00:00:00"))
        self.ip_lbl.setText(f"IP: {stats.get('ip', '')}")
        self.ping_lbl.setText(f"Ping: {stats.get('ping', '')}")

    def _on_server_selected(self, item: QListWidgetItem):
        srv_id = item.data(Qt.UserRole)
        self.vpn.set_server(srv_id)

    def _on_proto_changed(self, text: str):
        proto = "WireGuard" if "WireGuard" in text else ("Stealth" if "Stealth" in text else "OpenVPN")
        self.vpn.set_protocol(proto)


class HistoryVaultDialog(QDialog):
    """AES-256-GCM Encrypted History Vault dialog with password unlock and search."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_mgr = HistoryManager.get_instance()
        self.vault = self.history_mgr.vault
        self.drive_sync = self.history_mgr.drive_sync

        self.setWindowTitle("Lock Down Encrypted History Vault")
        self.setWindowIcon(get_icon("lock.svg"))
        self.resize(760, 580)
        self.setStyleSheet(f"background-color: {COLOR_BLUE_DARK}; color: {COLOR_IVORY_LIGHT};")

        self._build_ui()

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(14)

        if not self.vault.is_unlocked():
            self._build_locked_view()
        else:
            self._build_unlocked_view()

    def _build_locked_view(self):
        self._clear_layout()

        center_card = QFrame()
        center_card.setStyleSheet(f"background: {COLOR_BLUE_BASE}; border-radius: 16px; border: 1.5px solid {COLOR_BLUE_BORDER}; padding: 24px;")
        c_layout = QVBoxLayout(center_card)
        c_layout.setSpacing(14)
        c_layout.setAlignment(Qt.AlignCenter)

        lock_icon = QLabel()
        lock_icon.setPixmap(get_icon("lock.svg").pixmap(48, 48))
        lock_icon.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(lock_icon)

        title = QLabel("ENCRYPTED VAULT LOCKED")
        title.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {COLOR_CORAL_PRIMARY}; text-align: center;")
        title.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(title)

        desc = QLabel(
            "Your browsing & search history is encrypted with AES-256-GCM.\n"
            "Enter your Master Password or Private Key to unlock."
        )
        desc.setStyleSheet(f"font-size: 13px; color: {COLOR_IVORY_MUTED}; text-align: center;")
        desc.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(desc)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Enter Master Password or Private Key (LK-XXXX...)")
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setStyleSheet(f"padding: 10px 14px; background: {COLOR_BLUE_DARK}; border: 1px solid {COLOR_BLUE_BORDER}; border-radius: 8px; font-size: 14px;")
        self.pass_input.returnPressed.connect(self._try_unlock)
        c_layout.addWidget(self.pass_input)

        unlock_btn = QPushButton("Unlock Vault")
        unlock_btn.setStyleSheet(f"background: {COLOR_CORAL_PRIMARY}; color: #FFFFFF; font-weight: 800; padding: 10px; border-radius: 8px; font-size: 14px;")
        unlock_btn.clicked.connect(self._try_unlock)
        c_layout.addWidget(unlock_btn)

        self.main_layout.addStretch()
        self.main_layout.addWidget(center_card)
        self.main_layout.addStretch()

    def _build_unlocked_view(self):
        self._clear_layout()

        # Top Bar
        top_bar = QHBoxLayout()
        lock_icon = QLabel()
        lock_icon.setPixmap(get_icon("history.svg").pixmap(26, 26))
        top_bar.addWidget(lock_icon)

        vault_title = QLabel("SECURE ENCRYPTED VAULT")
        vault_title.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {COLOR_CORAL_PRIMARY}; letter-spacing: 1px;")
        top_bar.addWidget(vault_title)

        top_bar.addStretch()

        settings = load_settings()
        mode_text = "Google Drive Sync" if settings.get("history_storage_mode") == "gdrive" else "Local Secure Folder"
        mode_badge = QLabel(f"Storage: {mode_text}")
        mode_badge.setStyleSheet(f"background: {COLOR_BLUE_SURFACE}; color: {COLOR_IVORY_LIGHT}; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 600;")
        top_bar.addWidget(mode_badge)

        lock_btn = QPushButton("Lock Vault")
        lock_btn.setStyleSheet(f"background: {COLOR_BLUE_SURFACE}; color: {COLOR_CORAL_PRIMARY}; border: 1px solid {COLOR_BLUE_BORDER}; padding: 5px 12px;")
        lock_btn.clicked.connect(self._lock_vault)
        top_bar.addWidget(lock_btn)
        self.main_layout.addLayout(top_bar)

        # Search & Filter
        filter_box = QHBoxLayout()
        self.search_filter = QLineEdit()
        self.search_filter.setPlaceholderText("Filter history by search query, website, or keyword...")
        self.search_filter.setStyleSheet(f"background: {COLOR_BLUE_BASE}; border: 1px solid {COLOR_BLUE_BORDER}; border-radius: 8px; padding: 8px 12px;")
        self.search_filter.textChanged.connect(self._populate_records)
        filter_box.addWidget(self.search_filter, 1)

        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItems(["All Items", "Searches Only", "Websites Only"])
        self.filter_type_combo.currentTextChanged.connect(self._populate_records)
        filter_box.addWidget(self.filter_type_combo)
        self.main_layout.addLayout(filter_box)

        # Table of Records
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Time", "Type", "Title / Search Query", "URL"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.main_layout.addWidget(self.table, 1)

        # Bottom Actions Bar
        bottom_bar = QHBoxLayout()

        clear_btn = QPushButton("Clear History...")
        clear_btn.setStyleSheet(f"background: {COLOR_BLUE_SURFACE}; color: #FF6B4A; border: 1px solid {COLOR_BLUE_BORDER}; padding: 6px 12px;")
        clear_btn.clicked.connect(self._show_clear_menu)
        bottom_bar.addWidget(clear_btn)

        pkey_btn = QPushButton("Show Master Private Key")
        pkey_btn.setStyleSheet(f"background: {COLOR_BLUE_SURFACE}; color: {COLOR_IVORY_LIGHT}; border: 1px solid {COLOR_BLUE_BORDER}; padding: 6px 12px;")
        pkey_btn.clicked.connect(self._show_private_key)
        bottom_bar.addWidget(pkey_btn)

        bottom_bar.addStretch()

        sync_btn = QPushButton("Sync to Google Drive")
        sync_btn.setStyleSheet(f"background: {COLOR_CORAL_PRIMARY}; color: #FFFFFF; font-weight: 700; padding: 6px 14px; border-radius: 6px;")
        sync_btn.clicked.connect(self._sync_drive)
        bottom_bar.addWidget(sync_btn)

        self.main_layout.addLayout(bottom_bar)
        self._populate_records()

    def _clear_layout(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _try_unlock(self):
        entered = self.pass_input.text().strip()
        if not entered:
            return

        if entered.startswith("LK-"):
            ok = self.vault.unlock_with_private_key(entered)
        else:
            ok = self.vault.unlock_with_password(entered)

        if ok:
            self._build_unlocked_view()
        else:
            QMessageBox.warning(self, "Access Denied", "Incorrect Master Password or Private Key.")

    def _lock_vault(self):
        self.vault.lock()
        self._build_locked_view()

    def _populate_records(self):
        query = self.search_filter.text()
        f_type = self.filter_type_combo.currentText()
        type_param = "search" if "Searches" in f_type else ("pages" if "Websites" in f_type else "all")

        records = self.history_mgr.get_entries(search_text=query, filter_type=type_param)
        self.table.setRowCount(len(records))

        for row, r in enumerate(records):
            time_item = QTableWidgetItem(r.get("time_short", ""))
            type_item = QTableWidgetItem("🔍 Search" if r.get("is_search") else "🌐 Page")

            display_title = f"'{r.get('search_query')}'" if r.get("is_search") else r.get("title", "")
            title_item = QTableWidgetItem(display_title)
            url_item = QTableWidgetItem(r.get("url", ""))

            self.table.setItem(row, 0, time_item)
            self.table.setItem(row, 1, type_item)
            self.table.setItem(row, 2, title_item)
            self.table.setItem(row, 3, url_item)

    def _show_private_key(self):
        pkey = self.vault.get_current_private_key()
        if not pkey:
            pkey = "Vault is locked."

        QMessageBox.information(
            self,
            "Master Private Key",
            f"Your AES-256 Master Private Key is:\n\n{pkey}\n\n"
            "Keep this key safe. You can use it to decrypt your history on any device.",
        )

    def _show_clear_menu(self):
        ret = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear browsing history?\nThis will remove records from the encrypted vault.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ret == QMessageBox.Yes:
            self.history_mgr.clear_history("all")
            self._populate_records()
            QMessageBox.information(self, "History Cleared", "Encrypted history vault wiped.")

    def _sync_drive(self):
        ok, msg = self.drive_sync.test_connection()
        if not ok:
            QMessageBox.information(
                self,
                "Google Drive Sync",
                f"Cloud status: {msg}\n\n"
                "To configure your Google Drive API token or client secret, open Settings > History & Sync.",
            )
            return

        success, result_msg = self.drive_sync.sync_vault_to_drive()
        QMessageBox.information(self, "Google Drive Sync", result_msg)


class SettingsDialog(QDialog):
    """Main Settings dialog covering History Vault storage, Shields, VPN, and Search Engine."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Lock Down Browser Settings")
        self.setWindowIcon(get_icon("settings.svg"))
        self.resize(680, 520)
        self.setStyleSheet(f"background-color: {COLOR_BLUE_DARK}; color: {COLOR_IVORY_LIGHT};")

        self.settings = load_settings()
        self.vault = CryptoVault()
        self.drive_sync = GoogleDriveSync()

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_history_tab(), "🔒 History & Vault Storage")
        self.tabs.addTab(self._build_shields_tab(), "🛡️ Shields (uBlock Lite)")
        self.tabs.addTab(self._build_vpn_tab(), "🌐 Proton VPN")
        self.tabs.addTab(self._build_ai_tab(), "✨ Gemini AI")
        self.tabs.addTab(self._build_extensions_tab(), "🧩 Extensions")
        self.tabs.addTab(self._build_general_tab(), "⚙️ General")
        layout.addWidget(self.tabs, 1)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(cancel_btn)

        save_btn = QPushButton("Save Settings")
        save_btn.setStyleSheet(f"background: {COLOR_CORAL_PRIMARY}; color: #FFFFFF; font-weight: 700; padding: 8px 18px; border-radius: 6px;")
        save_btn.clicked.connect(self._save_and_close)
        btn_box.addWidget(save_btn)
        layout.addLayout(btn_box)

    def _build_history_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(16)

        # Storage Option
        grp = QGroupBox("Search History Storage Option")
        grp_layout = QVBoxLayout(grp)

        self.rb_local = QRadioButton("Store History Locally in Secure Password-Protected Folder")
        self.rb_local.setChecked(self.settings.get("history_storage_mode", "local") == "local")
        grp_layout.addWidget(self.rb_local)

        local_desc = QLabel(
            f"Automatically creates a secure, password-protected directory on your device:\n"
            f"Path: {VAULT_DIR}\n"
            f"Encryption: AES-256-GCM Authenticated Encryption with 200,000 PBKDF2 rounds."
        )
        local_desc.setStyleSheet(f"font-size: 11px; color: {COLOR_IVORY_MUTED}; margin-left: 20px; margin-bottom: 8px;")
        grp_layout.addWidget(local_desc)

        self.rb_gdrive = QRadioButton("Store History in Server / Google Drive of the User")
        self.rb_gdrive.setChecked(self.settings.get("history_storage_mode", "local") == "gdrive")
        grp_layout.addWidget(self.rb_gdrive)

        gdrive_desc = QLabel(
            "Uploads encrypted vault file to your Google Drive folder.\n"
            "Zero-Knowledge Guarantee: History is encrypted locally with your Private Key BEFORE uploading."
        )
        gdrive_desc.setStyleSheet(f"font-size: 11px; color: {COLOR_IVORY_MUTED}; margin-left: 20px;")
        grp_layout.addWidget(gdrive_desc)
        layout.addWidget(grp)

        # Private Key & Password setup
        sec_grp = QGroupBox("Master Password & Private Key")
        sec_layout = QFormLayout(sec_grp)

        self.pass_edit = QLineEdit()
        self.pass_edit.setPlaceholderText("Set or change Master Password")
        self.pass_edit.setEchoMode(QLineEdit.Password)
        sec_layout.addRow("New Master Password:", self.pass_edit)

        pkey_row = QHBoxLayout()
        current_pkey = self.vault.get_current_private_key() or "Unlock vault to view"
        self.lbl_pkey = QLabel(current_pkey)
        self.lbl_pkey.setStyleSheet(f"font-family: monospace; color: {COLOR_CORAL_PRIMARY}; font-weight: 700;")
        pkey_row.addWidget(self.lbl_pkey)

        copy_btn = QPushButton("Copy Key")
        copy_btn.clicked.connect(lambda: QMessageBox.information(self, "Key", f"Private Key:\n{self.lbl_pkey.text()}"))
        pkey_row.addWidget(copy_btn)
        sec_layout.addRow("Current Private Key:", pkey_row)
        layout.addWidget(sec_grp)

        # Google Drive credentials
        drive_grp = QGroupBox("Google Drive Server Integration")
        d_layout = QFormLayout(drive_grp)

        self.drive_folder_input = QLineEdit(self.settings.get("gdrive_folder_name", "LockDown_Secure_Vault"))
        d_layout.addRow("Drive Folder Name:", self.drive_folder_input)

        cred_row = QHBoxLayout()
        self.cred_path_input = QLineEdit(self.settings.get("gdrive_credentials_path", ""))
        cred_row.addWidget(self.cred_path_input, 1)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_credentials)
        cred_row.addWidget(browse_btn)
        d_layout.addRow("OAuth Client Secrets:", cred_row)

        test_btn = QPushButton("Test Google Drive Connection")
        test_btn.clicked.connect(self._test_gdrive)
        d_layout.addRow("", test_btn)
        layout.addWidget(drive_grp)

        layout.addStretch()
        return w

    def _browse_credentials(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Google OAuth credentials.json", "", "JSON Files (*.json)")
        if path:
            self.cred_path_input.setText(path)

    def _test_gdrive(self):
        ok, msg = self.drive_sync.test_connection()
        QMessageBox.information(self, "Google Drive Test", f"Result: {msg}")

    def _build_shields_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(14)

        self.cb_shields = QCheckBox("Enable Lock Down Shields Master Engine (uBlock Origin Lite inspired)")
        self.cb_shields.setChecked(self.settings.get("shields_enabled", True))
        layout.addWidget(self.cb_shields)

        self.cb_adblock = QCheckBox("Block Invasive Advertisements and Video Ads")
        self.cb_adblock.setChecked(self.settings.get("ad_blocking", True))
        layout.addWidget(self.cb_adblock)

        self.cb_trackers = QCheckBox("Block Cross-Site Telemetry & Fingerprinting Trackers")
        self.cb_trackers.setChecked(self.settings.get("tracker_blocking", True))
        layout.addWidget(self.cb_trackers)

        self.cb_cookies = QCheckBox("Auto-Block & Dismiss GDPR/Cookie Consent Overlays")
        self.cb_cookies.setChecked(self.settings.get("cookie_banner_blocking", True))
        layout.addWidget(self.cb_cookies)

        self.cb_https = QCheckBox("Enforce HTTPS Connections Only")
        self.cb_https.setChecked(self.settings.get("https_upgrade", True))
        layout.addWidget(self.cb_https)

        layout.addStretch()
        return w

    def _build_vpn_tab(self) -> QWidget:
        w = QWidget()
        layout = QFormLayout(w)
        layout.setSpacing(14)

        self.vpn_server_combo = QComboBox()
        for s in PROTON_SERVERS:
            self.vpn_server_combo.addItem(f"{s['flag']} {s['name']} ({s['tier']})", s["id"])
        idx = self.vpn_server_combo.findData(self.settings.get("vpn_server", "switzerland"))
        if idx >= 0:
            self.vpn_server_combo.setCurrentIndex(idx)
        layout.addRow("Default Secure Server:", self.vpn_server_combo)

        self.vpn_proto_combo = QComboBox()
        self.vpn_proto_combo.addItems(["WireGuard", "Stealth", "OpenVPN"])
        self.vpn_proto_combo.setCurrentText(self.settings.get("vpn_protocol", "WireGuard"))
        layout.addRow("Tunnel Protocol:", self.vpn_proto_combo)

        self.vpn_kill_cb = QCheckBox("Enable Network Kill Switch on startup")
        self.vpn_kill_cb.setChecked(self.settings.get("vpn_kill_switch", False))
        layout.addRow("Leak Protection:", self.vpn_kill_cb)

        self.vpn_proxy_input = QLineEdit(self.settings.get("vpn_custom_proxy", ""))
        self.vpn_proxy_input.setPlaceholderText("e.g. 127.0.0.1:1080 (Optional SOCKS5 Proxy)")
        layout.addRow("Custom Proxy:", self.vpn_proxy_input)

        return w

    def _build_general_tab(self) -> QWidget:
        w = QWidget()
        layout = QFormLayout(w)
        layout.setSpacing(14)

        self.engine_combo = QComboBox()
        for name in SEARCH_ENGINES.keys():
            self.engine_combo.addItem(name)
        self.engine_combo.setCurrentText(self.settings.get("search_engine", "Google"))
        layout.addRow("Default Search Engine:", self.engine_combo)

        self.cb_vertical = QCheckBox("Use Vertical Sidebar Tabs (Zen Style)")
        self.cb_vertical.setChecked(self.settings.get("vertical_tabs", False))
        layout.addRow("Tab Layout:", self.cb_vertical)

        self.cb_doh = QCheckBox("Enable Encrypted DNS-over-HTTPS (DoH via Cloudflare)")
        self.cb_doh.setChecked(self.settings.get("doh_enabled", True))
        layout.addRow("DNS Privacy:", self.cb_doh)

        return w

    def _build_ai_tab(self) -> QWidget:
        w = QWidget()
        layout = QFormLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        from lockdown.gemini_service import GeminiService, SUPPORTED_MODELS
        gem_svc = GeminiService.get_instance()

        self.gemini_key_edit = QLineEdit()
        self.gemini_key_edit.setEchoMode(QLineEdit.Password)
        self.gemini_key_edit.setPlaceholderText("Paste Gemini API Key from Google AI Studio")
        self.gemini_key_edit.setText(gem_svc.get_api_key())
        layout.addRow("Gemini API Key:", self.gemini_key_edit)

        self.gemini_model_combo = QComboBox()
        cur_model = gem_svc.get_model()
        for idx, m in enumerate(SUPPORTED_MODELS):
            self.gemini_model_combo.addItem(f"{m['name']} ({m['tag']})", m["id"])
            if m["id"] == cur_model:
                self.gemini_model_combo.setCurrentIndex(idx)
        layout.addRow("Active Vision Model:", self.gemini_model_combo)

        self.cb_view_browser = QCheckBox("Enable Browser Viewport Vision by Default")
        self.cb_view_browser.setChecked(self.settings.get("gemini_view_browser", True))
        layout.addRow("Vision Reasoning:", self.cb_view_browser)

        test_btn = QPushButton("Test Gemini Connection")
        test_btn.clicked.connect(self._test_gemini_key)
        layout.addRow("", test_btn)

        ai_studio_link = QPushButton("Get Free API Key from Google AI Studio")
        ai_studio_link.setStyleSheet(f"color: {COLOR_CORAL_PRIMARY}; text-align: left; font-weight: 700; background: transparent; border: none;")
        ai_studio_link.setCursor(Qt.PointingHandCursor)
        ai_studio_link.clicked.connect(self._open_ai_studio_tab)
        layout.addRow("", ai_studio_link)

        return w

    def _test_gemini_key(self):
        from lockdown.gemini_service import GeminiService
        key = self.gemini_key_edit.text().strip()
        valid, msg, models = GeminiService.get_instance().validate_api_key(key)
        if valid:
            QMessageBox.information(self, "Gemini Connected", f"{msg}\nAvailable vision models: {', '.join(models[:4])}")
        else:
            QMessageBox.warning(self, "Connection Error", msg)

    def _open_ai_studio_tab(self):
        parent = self.parent()
        if hasattr(parent, "add_tab"):
            parent.add_tab("https://aistudio.google.com/app/apikey", "Google AI Studio")

    def _build_extensions_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        from lockdown.extension_manager import ExtensionManager
        mgr = ExtensionManager.get_instance()
        installed = mgr.get_installed()

        desc = QLabel(f"Extensions enhance your browsing with dark mode, ad cleaning, reader views, and developer tools.\nCurrently {len(installed)} extensions installed.")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        open_hub_btn = QPushButton("🚀 Open Extensions Hub & Store (lockdown://extensions)")
        open_hub_btn.setStyleSheet(f"background: {COLOR_CORAL_PRIMARY}; color: white; font-weight: 700; padding: 10px; border-radius: 8px;")
        open_hub_btn.setCursor(Qt.PointingHandCursor)
        open_hub_btn.clicked.connect(self._open_extensions_hub)
        layout.addWidget(open_hub_btn)

        self.cb_ext_enable = QCheckBox("Enable WebExtensions Engine")
        self.cb_ext_enable.setChecked(self.settings.get("extensions_enabled", True))
        layout.addWidget(self.cb_ext_enable)

        layout.addStretch()
        return w

    def _open_extensions_hub(self):
        self.accept()
        parent = self.parent()
        if hasattr(parent, "navigate_url"):
            parent.navigate_url("lockdown://extensions")

    def _save_and_close(self):
        self.settings["history_storage_mode"] = "gdrive" if self.rb_gdrive.isChecked() else "local"
        self.settings["gdrive_folder_name"] = self.drive_folder_input.text().strip()
        self.settings["gdrive_credentials_path"] = self.cred_path_input.text().strip()

        # Update Master Password if entered
        new_pass = self.pass_edit.text().strip()
        if new_pass:
            ok, msg, pkey = self.vault.setup_vault(new_pass)
            if ok:
                QMessageBox.information(self, "Vault Updated", f"Master password updated.\nYour Private Key is:\n{pkey}")

        # Shields
        self.settings["shields_enabled"] = self.cb_shields.isChecked()
        self.settings["ad_blocking"] = self.cb_adblock.isChecked()
        self.settings["tracker_blocking"] = self.cb_trackers.isChecked()
        self.settings["cookie_banner_blocking"] = self.cb_cookies.isChecked()
        self.settings["https_upgrade"] = self.cb_https.isChecked()

        # VPN
        self.settings["vpn_server"] = self.vpn_server_combo.currentData()
        self.settings["vpn_protocol"] = self.vpn_proto_combo.currentText()
        self.settings["vpn_kill_switch"] = self.vpn_kill_cb.isChecked()
        self.settings["vpn_custom_proxy"] = self.vpn_proxy_input.text().strip()

        # Gemini AI & Extensions
        if hasattr(self, "gemini_key_edit"):
            from lockdown.gemini_service import GeminiService
            k = self.gemini_key_edit.text().strip()
            GeminiService.get_instance().set_api_key(k)
            self.settings["gemini_api_key"] = k
            m = self.gemini_model_combo.currentData()
            GeminiService.get_instance().set_model(m)
            self.settings["gemini_model"] = m
            self.settings["gemini_view_browser"] = self.cb_view_browser.isChecked()

        if hasattr(self, "cb_ext_enable"):
            self.settings["extensions_enabled"] = self.cb_ext_enable.isChecked()

        # General
        self.settings["search_engine"] = self.engine_combo.currentText()
        self.settings["vertical_tabs"] = self.cb_vertical.isChecked()
        self.settings["doh_enabled"] = self.cb_doh.isChecked()

        save_settings(self.settings)
        self.accept()


class FlowNotesPanel(QWidget):
    """Opera Flow inspired persistent notes & links sidebar scratchpad."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.notes: List[Dict[str, str]] = load_flow_notes()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        header = QLabel("QUICK FLOW NOTES")
        header.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {COLOR_CORAL_PRIMARY}; letter-spacing: 1px;")
        layout.addWidget(header)

        self.note_input = QTextEdit()
        self.note_input.setPlaceholderText("Write thoughts, paste URLs or code...")
        self.note_input.setFixedHeight(80)
        self.note_input.setStyleSheet(f"background: {COLOR_BLUE_BASE}; border: 1px solid {COLOR_BLUE_BORDER}; border-radius: 8px; color: {COLOR_IVORY_LIGHT};")
        layout.addWidget(self.note_input)

        add_btn = QPushButton("+ Add Note")
        add_btn.setStyleSheet(f"background: {COLOR_CORAL_PRIMARY}; color: #FFFFFF; font-weight: 700; border-radius: 6px; padding: 6px;")
        add_btn.clicked.connect(self._add_note)
        layout.addWidget(add_btn)

        self.notes_list = QListWidget()
        self.notes_list.setStyleSheet(f"background: {COLOR_BLUE_BASE}; border: 1px solid {COLOR_BLUE_BORDER}; border-radius: 8px;")
        layout.addWidget(self.notes_list, 1)

        clear_btn = QPushButton("Clear All Notes")
        clear_btn.setStyleSheet(f"background: {COLOR_BLUE_SURFACE}; color: {COLOR_IVORY_MUTED}; border: 1px solid {COLOR_BLUE_BORDER}; padding: 4px;")
        clear_btn.clicked.connect(self._clear_notes)
        layout.addWidget(clear_btn)

        self._refresh_list()

    def _add_note(self):
        text = self.note_input.toPlainText().strip()
        if not text:
            return
        from datetime import datetime
        entry = {"text": text, "time": datetime.now().strftime("%b %d, %H:%M")}
        self.notes.insert(0, entry)
        save_flow_notes(self.notes)
        self.note_input.clear()
        self._refresh_list()

    def _clear_notes(self):
        self.notes = []
        save_flow_notes(self.notes)
        self._refresh_list()

    def _refresh_list(self):
        self.notes_list.clear()
        for n in self.notes:
            item = QListWidgetItem(f"[{n.get('time', '')}]\n{n.get('text', '')}")
            self.notes_list.addItem(item)
