"""Lock Down Browser - Main Application Entrypoint.
High-Security Editorial Browser with Brave Shields, Opera Workspaces, Zen Focus,
Gemini AI Vision Intelligence, and AES-256-GCM Encrypted Vault with Proton VPN.
Powered by modern Chromium engine.
"""

import sys

# Import Qt compatibility layer first (initializes PyQt6 Chromium 140 / PyQt5)
from lockdown.qt_compat import Qt, QApplication
from lockdown.config import APP_NAME
from lockdown.icons import get_app_icon
from lockdown.ui.main_window import LockDownBrowserWindow


def main():
    # Enable high-DPI scaling and OpenGL sharing if supported
    for attr_name in ("AA_EnableHighDpiScaling", "AA_UseHighDpiPixmaps", "AA_ShareOpenGLContexts"):
        try:
            attr = getattr(Qt, attr_name, None)
            if attr is not None:
                QApplication.setAttribute(attr, True)
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setWindowIcon(get_app_icon())

    window = LockDownBrowserWindow(is_private=False)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
