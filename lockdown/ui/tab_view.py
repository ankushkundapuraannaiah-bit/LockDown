"""Lock Down Custom WebEngine Tab and Page.
Integrates uBlock Origin Lite cosmetic script injection,
encrypted history recording with zero-storage private mode, and snapshot tools.
Uses Chromium-class engine settings to present as a first-class browser (Brave/Opera style).
"""

from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

from lockdown.qt_compat import (
    QAction,
    QApplication,
    QColor,
    QDateTime,
    QFileDialog,
    QIcon,
    QImage,
    QMenu,
    QMessageBox,
    QPainter,
    QPixmap,
    QSize,
    Qt,
    QUrl,
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineScript,
    QWebEngineSettings,
    QWebEngineView,
    pyqtSignal,
)

from lockdown.blocker import COSMETIC_INJECT_JS
from lockdown.config import (
    SEARCH_ENGINES,
    load_settings,
)
from lockdown.history_manager import HistoryManager
from lockdown.home_server import get_downloads_url, get_extensions_url, get_home_url, get_settings_url

# ---------------------------------------------------------------------------
# SEARCH ENGINE DESKTOP OPTIMIZER
# Clean, non-destructive script that preserves search engines' native responsive
# desktop layouts (Google Web & Images, Brave, DuckDuckGo, Bing).
# ---------------------------------------------------------------------------
SEARCH_DESKTOP_OPTIMIZE_JS = r"""
(function() {
  'use strict';
  try {
    const host = location.hostname.replace(/^www\./, '');
    const isGoogle = /^(google\.[a-z.]+)$/.test(host);
    const isBrave = host === 'search.brave.com';
    const isDDG = host === 'duckduckgo.com';
    const isBing = host === 'bing.com' || host.endsWith('.bing.com');
    const isSearchEngine = isGoogle || isBrave || isDDG || isBing;

    // IMPORTANT: If not on a recognized search engine, do NOT apply any overrides.
    // This protects non-search sites like GitHub, ChatGPT, etc. from selector leaks.
    if (!isSearchEngine) return;

    // 1. Additive CSS adjustments - scoped strictly per engine
    if (!document.getElementById('ld-search-style')) {
      const s = document.createElement('style');
      s.id = 'ld-search-style';
      let css = '';

      if (isGoogle) {
        css += `
          /* Google Web Search - keep RHS knowledge panel visible on wide screens */
          @media (min-width: 1080px) {
            #rhs {
              display: block !important;
              visibility: visible !important;
            }
          }
        `;
      }

      if (isBrave) {
        css += `
          /* Brave Search - responsive horizontal tab strip */
          #primary-tabs, nav.tabs, .tabs-wrapper, .search-tabs, .filters-bar {
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            gap: 8px !important;
            list-style: none !important;
            padding: 0 !important;
            margin: 6px 0 !important;
            overflow-x: auto !important;
            scrollbar-width: none !important;
          }
          .tab-item, li.tab-item {
            display: inline-flex !important;
            align-items: center !important;
            margin: 0 !important;
          }
          .tab-item a, li.tab-item a,
          .tabs-wrapper a, .search-tabs a, .filters-bar a {
            display: inline-flex !important;
            align-items: center !important;
            padding: 6px 14px !important;
            margin: 0 4px !important;
            border-radius: 18px !important;
            white-space: nowrap !important;
            font-size: 13.5px !important;
            font-weight: 500 !important;
            text-decoration: none !important;
            color: #4b5563 !important;
            background: #f3f4f6 !important;
            transition: background 0.2s !important;
          }
          .tab-item a:hover, li.tab-item a:hover {
            background: #e5e7eb !important;
            color: #111827 !important;
          }

          /* Brave Search Images Grid & Alignment */
          .layout-wrapper, .images-layout-wrapper, .images-layout {
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            display: block !important;
          }
          .layout-wrapper > .layout,
          .layout-wrapper > div.layout,
          div.layout.type--hybrid {
            display: grid !important;
            grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)) !important;
            gap: 12px !important;
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            padding: 12px 16px !important;
          }
          .layout-wrapper .image-result,
          .images-layout .image-result,
          button.image-result,
          button[class*="image-result"] {
            display: flex !important;
            flex-direction: column !important;
            width: 100% !important;
            max-width: 100% !important;
            height: 230px !important;
            margin: 0 !important;
            padding: 0 !important;
            background: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 8px !important;
            overflow: hidden !important;
            cursor: pointer !important;
            box-sizing: border-box !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
            transition: transform 0.15s ease, box-shadow 0.15s ease !important;
          }
          .layout-wrapper .image-result:hover,
          button.image-result:hover,
          button[class*="image-result"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.12) !important;
          }
          .image-result .image-wrapper,
          [class*="image-wrapper"] {
            display: flex !important;
            width: 100% !important;
            height: 180px !important;
            flex: 1 1 180px !important;
            background: #f9fafb !important;
            align-items: center !important;
            justify-content: center !important;
            overflow: hidden !important;
          }
          .image-result .image-wrapper img,
          [class*="image-wrapper"] img {
            width: 100% !important;
            height: 100% !important;
            max-height: 180px !important;
            object-fit: cover !important;
            display: block !important;
          }
          .image-result .image-metadata,
          [class*="image-metadata"] {
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            width: 100% !important;
            height: 48px !important;
            padding: 4px 8px !important;
            box-sizing: border-box !important;
            background: #ffffff !important;
            text-align: left !important;
            overflow: hidden !important;
          }
          .image-result .image-metadata-site,
          [class*="image-metadata-site"] {
            font-size: 11px !important;
            color: #6b7280 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
          }
          .image-result .image-metadata-title,
          [class*="image-metadata-title"] {
            font-size: 12px !important;
            font-weight: 600 !important;
            color: #1f2937 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
          }
        `;
      }

      if (isDDG) {
        css += `
          /* DuckDuckGo - Sticky Navigation Bar & Menu Bar */
          html, body, .site-wrapper {
            overflow: visible !important;
          }
          #header_wrapper, .header-wrap, .js-header-wrap, #header {
            position: sticky !important;
            top: 0 !important;
            z-index: 9999 !important;
            background: var(--theme-col-bg, #ffffff) !important;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08) !important;
          }
          #header nav, .header-wrap nav, [data-testid="navigation-bar"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
          }
          .results--main { max-width: 1400px !important; }
          .zcm__tabs { display: flex !important; gap: 6px !important; flex-wrap: nowrap !important; }
          [class*="modal_upgrade"], [class*="badge-link"], div[class*="modal-dialog"] {
            display: none !important;
            visibility: hidden !important;
            pointer-events: none !important;
          }
        `;
      }

      if (isBing) {
        css += `
          /* Bing scopebar */
          .b_scopebar { display: flex !important; gap: 4px !important; align-items: center !important; }
        `;
      }

      s.textContent = css;
      (document.head || document.documentElement).appendChild(s);
    }

    // 2. Unhide Google RHS if marked hidden by responsive classes (only on web search)
    if (isGoogle) {
      const params = new URLSearchParams(location.search);
      const isImages = params.get('tbm') === 'isch' || params.get('udm') === '2';
      if (!isImages) {
        const rhs = document.getElementById('rhs');
        if (rhs && rhs.classList.contains('vVVcqf')) {
          rhs.classList.remove('vVVcqf');
          rhs.classList.add('N4Xssf');
        }
      }
    }

    // 3. Resolve common deferred images that may have data-src without src
    function fixDeferredImages() {
      try {
        const lazyImgs = document.querySelectorAll('img[data-src]:not([src]), img[data-deferred-src]:not([src])');
        for (let i = 0; i < lazyImgs.length; i++) {
          const img = lazyImgs[i];
          const src = img.getAttribute('data-src') || img.getAttribute('data-deferred-src');
          if (src) {
            img.src = src;
          }
        }
      } catch(_) {}
    }

    fixDeferredImages();
    setTimeout(fixDeferredImages, 1500);

  } catch (_) {}
})();
"""


# ---------------------------------------------------------------------------
# ANTI-BOT STEALTH & SEARCH ENGINE VERIFICATION BYPASS
# Cloaks QtWebEngine/headless fingerprints, provides native Chromium 140 objects,
# and auto-accepts Google/Bing consent prompts so cookies (SOCS, CONSENT)
# persist without bot verification or CAPTCHA loops.
# ---------------------------------------------------------------------------
ANTI_BOT_STEALTH_JS = r"""
(function() {
  'use strict';
  try {
    // 1. Cloak navigator.webdriver
    try {
      Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true
      });
    } catch (_) {}

    // 2. Mock realistic plugins so navigator.plugins.length > 0 (prevents headless bot detection)
    try {
      if (!navigator.plugins || navigator.plugins.length === 0) {
        const dummyPlugins = [
          { name: 'PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
          { name: 'Chrome PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
          { name: 'Chromium PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
          { name: 'Microsoft Edge PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
          { name: 'WebKit built-in PDF', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }
        ];
        const pluginArray = Object.create(PluginArray.prototype || Array.prototype);
        dummyPlugins.forEach((p, idx) => {
          pluginArray[idx] = p;
          pluginArray[p.name] = p;
        });
        Object.defineProperty(pluginArray, 'length', { get: () => dummyPlugins.length });
        Object.defineProperty(navigator, 'plugins', {
          get: () => pluginArray,
          configurable: true
        });
      }
    } catch (_) {}

    // 3. Emulate standard window.chrome
    try {
      if (!window.chrome) {
        window.chrome = {};
      }
      if (!window.chrome.runtime) {
        window.chrome.runtime = {
          id: undefined,
          connect: function() {},
          sendMessage: function() {},
          onMessage: { addListener: function() {}, removeListener: function() {} }
        };
      }
      if (!window.chrome.loadTimes) {
        window.chrome.loadTimes = function() {
          const now = Date.now() / 1000;
          return {
            requestTime: now - 0.2,
            startLoadTime: now - 0.2,
            commitLoadTime: now - 0.1,
            finishDocumentLoadTime: now,
            finishLoadTime: now,
            firstPaintTime: now - 0.05,
            firstPaintAfterLoadTime: 0,
            navigationType: 'Other'
          };
        };
      }
      if (!window.chrome.csi) {
        window.chrome.csi = function() {
          return {
            startE: performance.timing ? performance.timing.navigationStart : Date.now(),
            onloadT: performance.timing ? performance.timing.domContentLoadedEventEnd : Date.now(),
            pageT: performance.now(),
            tran: 15
          };
        };
      }
      if (!window.chrome.app) {
        window.chrome.app = {
          isInstalled: false,
          InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' },
          RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' }
        };
      }
    } catch (_) {}

    // 4. Auto-consent for Google and Bing to establish SOCS/CONSENT cookies
    function autoAcceptSearchConsent() {
      try {
        const host = location.hostname.toLowerCase();
        if (host.includes('google.')) {
          // Google's canonical accept buttons: #L2AG9b, or button with text 'Accept all'
          const acceptBtn = document.querySelector('#L2AG9b, button[id="L2AG9b"], form[action*="consent"] button:last-child');
          if (acceptBtn && acceptBtn.offsetParent !== null) {
            acceptBtn.click();
          }
        } else if (host.includes('bing.com')) {
          // Bing consent
          const bingAccept = document.querySelector('#bnp_btn_accept, button#bnp_btn_accept');
          if (bingAccept && bingAccept.offsetParent !== null) {
            bingAccept.click();
          }
        }
      } catch (_) {}
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', autoAcceptSearchConsent);
    } else {
      autoAcceptSearchConsent();
    }
    setTimeout(autoAcceptSearchConsent, 400);
    setTimeout(autoAcceptSearchConsent, 1200);

  } catch (_) {}
})();
"""


def ensure_desktop_script_installed(profile: QWebEngineProfile):
    """Install search optimizer and anti-bot stealth scripts on a profile."""
    existing = {s.name() for s in profile.scripts().toList()}

    if "LockDownAntiBotStealth" not in existing:
        stealth_script = QWebEngineScript()
        stealth_script.setName("LockDownAntiBotStealth")
        stealth_script.setSourceCode(ANTI_BOT_STEALTH_JS)
        stealth_script.setInjectionPoint(QWebEngineScript.DocumentCreation)
        stealth_script.setWorldId(QWebEngineScript.MainWorld)
        stealth_script.setRunsOnSubFrames(True)
        profile.scripts().insert(stealth_script)

    if "LockDownSearchOptimize" not in existing:
        script = QWebEngineScript()
        script.setName("LockDownSearchOptimize")
        script.setSourceCode(SEARCH_DESKTOP_OPTIMIZE_JS)
        script.setInjectionPoint(QWebEngineScript.DocumentReady)
        script.setWorldId(QWebEngineScript.MainWorld)
        script.setRunsOnSubFrames(False)
        profile.scripts().insert(script)


class LockDownWebPage(QWebEnginePage):
    def __init__(self, tab_view: "LockDownTabView", profile: QWebEngineProfile, parent=None):
        super().__init__(profile, parent)
        self.tab_view = tab_view

    def createWindow(self, _window_type):
        if hasattr(self.tab_view.browser_window, "add_tab"):
            new_tab = self.tab_view.browser_window.add_tab(
                url="about:blank",
                background=False,
            )
            return new_tab.page()
        return None

    def certificateError(self, error):
        return False  # strict HTTPS — reject bad certs

    def acceptNavigationRequest(self, url: QUrl, nav_type: int, is_main_frame: bool) -> bool:
        # Never intercept Back/Forward or Reload
        if nav_type in (
            QWebEnginePage.NavigationTypeBackForward,
            QWebEnginePage.NavigationTypeReload,
        ):
            return super().acceptNavigationRequest(url, nav_type, is_main_frame)

        # Enforce HTTPS on top-level main frame navigation for external sites
        if is_main_frame and url.scheme() == "http":
            host = url.host().lower()
            if host not in ("localhost", "127.0.0.1", "::1", "") and not host.startswith(("192.168.", "10.")):
                secure_url = QUrl(url)
                secure_url.setScheme("https")
                self.load(secure_url)
                return False

        return super().acceptNavigationRequest(url, nav_type, is_main_frame)


class LockDownTabView(QWebEngineView):
    custom_title_changed = pyqtSignal(str)
    custom_url_changed   = pyqtSignal(QUrl)
    custom_icon_changed  = pyqtSignal(QIcon)

    def __init__(
        self,
        browser_window,
        profile: QWebEngineProfile,
        url: str = "lockdown://home",
        is_private: bool = False,
    ):
        super().__init__()
        self.browser_window = browser_window
        self.profile        = profile
        self.is_private     = is_private
        self.current_title  = "New Tab"

        # Custom page
        self.web_page = LockDownWebPage(self, profile, self)
        self.setPage(self.web_page)
        ensure_desktop_script_installed(self.profile)

        # Chromium-class settings
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled,             True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled,                True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows,      False)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled,      True)
        settings.setAttribute(QWebEngineSettings.ScreenCaptureEnabled,          True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled,           not is_private)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.DnsPrefetchEnabled,            False)
        self._set_attr(settings, "AutoLoadImages",             True)
        self._set_attr(settings, "AutoLoadIconsForPage",       True)
        self._set_attr(settings, "Accelerated2dCanvasEnabled", True)
        self._set_attr(settings, "WebGLEnabled",               True)
        self._set_attr(settings, "FocusOnNavigationEnabled",   True)
        self._set_attr(settings, "ScrollAnimatorEnabled",      True)
        self._set_attr(settings, "TouchIconsEnabled",          True)
        self._set_attr(settings, "ErrorPageEnabled",           True)
        self._set_attr(settings, "AllowRunningInsecureContent",False)
        if hasattr(QWebEngineSettings, "PlaybackRequiresUserGesture"):
            settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)

        self.setZoomFactor(1.0)

        # Signals
        self.urlChanged.connect(self._on_url_changed)
        self.titleChanged.connect(self._on_title_changed)
        self.iconChanged.connect(self.custom_icon_changed.emit)
        self.loadStarted.connect(self._on_load_started)
        self.loadFinished.connect(self._on_load_finished)

        self.navigate(url)

    @staticmethod
    def _set_attr(settings, name: str, value: bool):
        attr = getattr(QWebEngineSettings, name, None)
        if attr is not None:
            settings.setAttribute(attr, value)

    # backward compat alias
    @staticmethod
    def _set_setting_if_available(settings, name: str, value: bool):
        LockDownTabView._set_attr(settings, name, value)

    # ── Navigation ─────────────────────────────────────────────────────────
    def navigate(self, target: str):
        """Navigate to a URL or search query. HTTPS always enforced externally."""
        target = target.strip()
        if not target or target in ("lockdown://home", "lockdown://newtab", "about:blank"):
            self.setUrl(QUrl.fromUserInput(get_home_url()))
            return

        if target.lower() in ("lockdown://extensions", "about:extensions", "chrome://extensions"):
            self.setUrl(QUrl.fromUserInput(get_extensions_url()))
            return

        if target.lower() in ("lockdown://settings", "about:settings", "chrome://settings"):
            self.setUrl(QUrl.fromUserInput(get_settings_url()))
            return

        if target.lower() in ("lockdown://downloads", "about:downloads", "chrome://downloads"):
            self.setUrl(QUrl.fromUserInput(get_downloads_url()))
            return

        lower = target.lower()

        if lower.startswith(("file://", "data:")):
            self.setUrl(QUrl.fromUserInput(target))
            return

        if lower.startswith("http://"):
            domain = target[7:].split("/")[0].split(":")[0].lower()
            is_local = (
                domain in ("localhost", "127.0.0.1", "::1") or
                domain.startswith("192.168.") or
                domain.startswith("10.")
            )
            if not is_local:
                target = "https://" + target[7:]
            self.setUrl(QUrl.fromUserInput(target))
            return

        if lower.startswith("https://"):
            self.setUrl(QUrl.fromUserInput(target))
            return

        # Bare domain → default HTTPS
        if "." in target and " " not in target and not lower.startswith("localhost"):
            self.setUrl(QUrl.fromUserInput("https://" + target))
            return

        # Search query
        s           = load_settings()
        engine_name = s.get("search_engine", "Google")
        engine_info = SEARCH_ENGINES.get(engine_name, SEARCH_ENGINES["Google"])
        self.setUrl(QUrl.fromUserInput(
            engine_info["url"].format(query=quote_plus(target))
        ))

    # ── Signal handlers ────────────────────────────────────────────────────
    def _on_load_started(self):
        self._notify_nav_state()

    def _on_url_changed(self, qurl: QUrl):
        self.custom_url_changed.emit(qurl)
        self._notify_nav_state()
        url_str = qurl.toString()
        if not self._is_internal_url(url_str):
            HistoryManager.get_instance().record_visit(
                url=url_str,
                title=self.current_title,
                is_private=self.is_private,
            )

    def _on_title_changed(self, title: str):
        clean = title.strip() or "New Tab"
        self.current_title = clean
        self.custom_title_changed.emit(clean)
        url_str = self.url().toString()
        if not self._is_internal_url(url_str):
            HistoryManager.get_instance().record_visit(
                url=url_str,
                title=clean,
                is_private=self.is_private,
            )

    def _on_load_finished(self, success: bool):
        self._notify_nav_state()
        if success:
            try:
                self.page().runJavaScript(SEARCH_DESKTOP_OPTIMIZE_JS)
                self.page().runJavaScript(ANTI_BOT_STEALTH_JS)
                settings = load_settings()
                if settings.get("shields_enabled", True):
                    self.page().runJavaScript(COSMETIC_INJECT_JS)
            except Exception:
                pass

    def _notify_nav_state(self):
        """Notify the main window to update Back/Forward/Reload button states."""
        if hasattr(self.browser_window, "_refresh_nav_buttons"):
            self.browser_window._refresh_nav_buttons(self)

    @staticmethod
    def _is_internal_url(url_str: str) -> bool:
        return (
            url_str.startswith("file://")
            or url_str.startswith("lockdown://")
            or (
                "127.0.0.1:" in url_str
                and (
                    "/lockdown-home" in url_str
                    or "/lockdown-extensions" in url_str
                    or "/lockdown-settings" in url_str
                    or "/lockdown-downloads" in url_str
                )
            )
        )

    # ── Snapshot ───────────────────────────────────────────────────────────
    def take_snapshot(self):
        pixmap = self.grab()
        if pixmap.isNull():
            return
        default_name = (
            f"lockdown_snapshot_"
            f"{QDateTime.currentDateTime().toString('yyyyMMdd_hhmmss')}.png"
        )
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Tab Snapshot",
            str(Path.home() / "Pictures" / default_name),
            "PNG Image (*.png);;JPEG Image (*.jpg)",
        )
        if path:
            pixmap.save(path)
            QMessageBox.information(self, "Snapshot Saved", f"Saved snapshot to:\n{path}")
        else:
            QApplication.clipboard().setPixmap(pixmap)
            QMessageBox.information(self, "Snapshot Copied", "Snapshot copied to your clipboard.")

    # ── Context menu ───────────────────────────────────────────────────────
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        if hasattr(self.browser_window, "is_zen_mode") and self.browser_window.is_zen_mode:
            exit_act = menu.addAction("Exit Zen Focus Canvas (Esc)")
            exit_act.triggered.connect(self.browser_window._exit_zen_mode)
            menu.addSeparator()

        back_act = menu.addAction("Back")
        back_act.setEnabled(self.history().canGoBack())
        back_act.triggered.connect(lambda: self.triggerPageAction(QWebEnginePage.Back))

        fwd_act = menu.addAction("Forward")
        fwd_act.setEnabled(self.history().canGoForward())
        fwd_act.triggered.connect(lambda: self.triggerPageAction(QWebEnginePage.Forward))

        reload_act = menu.addAction("Reload")
        reload_act.triggered.connect(lambda: self.triggerPageAction(QWebEnginePage.Reload))

        menu.addSeparator()

        copy_act = menu.addAction("Copy Page URL")
        copy_act.triggered.connect(
            lambda: QApplication.clipboard().setText(self.url().toString())
        )
        snap_act = menu.addAction("Capture Page Snapshot")
        snap_act.triggered.connect(self.take_snapshot)

        menu.addSeparator()

        zi = menu.addAction("Zoom In (+)")
        zi.triggered.connect(lambda: self.setZoomFactor(self.zoomFactor() + 0.1))
        zo = menu.addAction("Zoom Out (-)")
        zo.triggered.connect(lambda: self.setZoomFactor(max(0.5, self.zoomFactor() - 0.1)))
        zr = menu.addAction("Reset Zoom (100%)")
        zr.triggered.connect(lambda: self.setZoomFactor(1.0))

        menu.exec_(event.globalPos())
