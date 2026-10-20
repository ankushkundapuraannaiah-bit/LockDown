"""Universal Qt Compatibility Layer for Lock Down Browser.
Supports PyQt6 (modern Chromium 140) with seamless fallback to PyQt5.
Provides normalized access to QtCore, QtGui, QtWidgets, QtWebEngineWidgets, and QtWebEngineCore.
"""

import sys

try:
    # ── Try PyQt6 first (Modern Chromium 140 Engine) ──────────────────────────
    import PyQt6.QtCore as _QtCore
    import PyQt6.QtGui as _QtGui
    import PyQt6.QtWidgets as _QtWidgets
    import PyQt6.QtWebEngineCore as _QtWebEngineCore
    import PyQt6.QtWebEngineWidgets as _QtWebEngineWidgets

    IS_PYQT6 = True

    # 1. Provide exec_ aliases on QDialog, QApplication, QMenu
    _QtWidgets.QApplication.exec_ = lambda self, *args, **kwargs: self.exec(*args, **kwargs)
    _QtWidgets.QDialog.exec_ = lambda self, *args, **kwargs: self.exec(*args, **kwargs)
    _QtWidgets.QMenu.exec_ = lambda self, *args, **kwargs: self.exec(*args, **kwargs)

    # 2. QAction in PyQt6 is in QtGui, alias into QtWidgets
    _QtWidgets.QAction = _QtGui.QAction

    # 3. Transparent QtProxy for unscoped enum lookups (e.g. Qt.AlignCenter, Qt.PointingHandCursor)
    class _QtProxy:
        def __init__(self):
            self._cache = {}
            for item_name in dir(_QtCore.Qt):
                item = getattr(_QtCore.Qt, item_name, None)
                if hasattr(item, "__members__"):
                    for m_name, m_val in item.__members__.items():
                        self._cache[m_name] = m_val
                elif isinstance(item, type):
                    for sub_name in dir(item):
                        if not sub_name.startswith("_"):
                            self._cache[sub_name] = getattr(item, sub_name)

        def __getattr__(self, name):
            if hasattr(_QtCore.Qt, name):
                return getattr(_QtCore.Qt, name)
            if name in self._cache:
                return self._cache[name]
            raise AttributeError(f"Qt has no attribute {name}")

        def __or__(self, other):
            return _QtCore.Qt | other

    Qt = _QtProxy()

    # 4. Map scoped enums onto classes (PyQt5-style flat access)
    import enum

    def _flatten_class_enums(cls):
        if not isinstance(cls, type):
            return
        for name in dir(cls):
            if name.startswith("_"):
                continue
            try:
                val = getattr(cls, name, None)
                if isinstance(val, type) and issubclass(val, enum.Enum):
                    for m_name, m_val in val.__members__.items():
                        if not hasattr(cls, m_name):
                            setattr(cls, m_name, m_val)
            except Exception:
                pass

    for _mod in (_QtCore, _QtGui, _QtWidgets, _QtWebEngineCore, _QtWebEngineWidgets):
        for _item_name in dir(_mod):
            if not _item_name.startswith("_"):
                _item = getattr(_mod, _item_name, None)
                if isinstance(_item, type):
                    _flatten_class_enums(_item)


    # Export classes
    QtCore = _QtCore
    QtGui = _QtGui
    QtWidgets = _QtWidgets
    QtWebEngineCore = _QtWebEngineCore
    QtWebEngineWidgets = _QtWebEngineWidgets

    # Direct common re-exports
    QUrl = _QtCore.QUrl
    QSize = _QtCore.QSize
    QPoint = _QtCore.QPoint
    QDateTime = _QtCore.QDateTime
    QTimer = _QtCore.QTimer
    QEvent = _QtCore.QEvent
    QBuffer = _QtCore.QBuffer
    QIODevice = _QtCore.QIODevice
    QThread = _QtCore.QThread
    pyqtSignal = _QtCore.pyqtSignal
    QObject = _QtCore.QObject

    QIcon = _QtGui.QIcon
    QColor = _QtGui.QColor
    QImage = _QtGui.QImage
    QPixmap = _QtGui.QPixmap
    QPainter = _QtGui.QPainter
    QFont = _QtGui.QFont
    QKeySequence = _QtGui.QKeySequence
    QAction = _QtGui.QAction
    QDesktopServices = _QtGui.QDesktopServices

    QApplication = _QtWidgets.QApplication
    QMainWindow = _QtWidgets.QMainWindow
    QWidget = _QtWidgets.QWidget
    QDialog = _QtWidgets.QDialog
    QMenu = _QtWidgets.QMenu
    QFrame = _QtWidgets.QFrame
    QHBoxLayout = _QtWidgets.QHBoxLayout
    QVBoxLayout = _QtWidgets.QVBoxLayout
    QLabel = _QtWidgets.QLabel
    QLineEdit = _QtWidgets.QLineEdit
    QPushButton = _QtWidgets.QPushButton
    QSizePolicy = _QtWidgets.QSizePolicy
    QMessageBox = _QtWidgets.QMessageBox
    QFileDialog = _QtWidgets.QFileDialog
    QStatusBar = _QtWidgets.QStatusBar
    QTabBar = _QtWidgets.QTabBar
    QTabWidget = _QtWidgets.QTabWidget
    QToolBar = _QtWidgets.QToolBar
    QDockWidget = _QtWidgets.QDockWidget
    QListWidget = _QtWidgets.QListWidget
    QListWidgetItem = _QtWidgets.QListWidgetItem
    QCompleter = _QtWidgets.QCompleter
    QButtonGroup = _QtWidgets.QButtonGroup
    QCheckBox = _QtWidgets.QCheckBox
    QComboBox = _QtWidgets.QComboBox
    QFormLayout = _QtWidgets.QFormLayout
    QGroupBox = _QtWidgets.QGroupBox
    QHeaderView = _QtWidgets.QHeaderView
    QRadioButton = _QtWidgets.QRadioButton
    QScrollArea = _QtWidgets.QScrollArea
    QTableWidget = _QtWidgets.QTableWidget
    QTableWidgetItem = _QtWidgets.QTableWidgetItem
    QTextEdit = _QtWidgets.QTextEdit
    QProgressBar = _QtWidgets.QProgressBar
    import PyQt6.QtNetwork as _QtNetwork

    if hasattr(_QtNetwork, "QNetworkProxy"):
        _ProxyType = getattr(_QtNetwork.QNetworkProxy, "ProxyType", None)
        if _ProxyType:
            for _a in dir(_ProxyType):
                if not _a.startswith("_"):
                    setattr(_QtNetwork.QNetworkProxy, _a, getattr(_ProxyType, _a))

    QNetworkProxy = _QtNetwork.QNetworkProxy

    QWebEngineView = _QtWebEngineWidgets.QWebEngineView
    QWebEnginePage = _QtWebEngineCore.QWebEnginePage
    QWebEngineProfile = _QtWebEngineCore.QWebEngineProfile
    if hasattr(_QtWebEngineCore.QWebEngineProfile, "setUrlRequestInterceptor") and not hasattr(_QtWebEngineCore.QWebEngineProfile, "setRequestInterceptor"):
        _QtWebEngineCore.QWebEngineProfile.setRequestInterceptor = lambda self, interceptor: self.setUrlRequestInterceptor(interceptor)
    QWebEngineScript = _QtWebEngineCore.QWebEngineScript
    QWebEngineSettings = _QtWebEngineCore.QWebEngineSettings
    QWebEngineUrlRequestInterceptor = _QtWebEngineCore.QWebEngineUrlRequestInterceptor
    QWebEngineUrlRequestInfo = _QtWebEngineCore.QWebEngineUrlRequestInfo
    QWebEngineDownloadRequest = getattr(_QtWebEngineCore, "QWebEngineDownloadRequest", None)

except ImportError:
    # ── Fallback to PyQt5 ─────────────────────────────────────────────────────
    import PyQt5.QtCore as _QtCore
    import PyQt5.QtGui as _QtGui
    import PyQt5.QtWidgets as _QtWidgets
    import PyQt5.QtWebEngineCore as _QtWebEngineCore
    import PyQt5.QtWebEngineWidgets as _QtWebEngineWidgets
    import PyQt5.QtNetwork as _QtNetwork

    IS_PYQT6 = False
    Qt = _QtCore.Qt

    QtCore = _QtCore
    QtGui = _QtGui
    QtWidgets = _QtWidgets
    QtWebEngineCore = _QtWebEngineCore
    QtWebEngineWidgets = _QtWebEngineWidgets
    QtNetwork = _QtNetwork

    QUrl = _QtCore.QUrl
    QSize = _QtCore.QSize
    QPoint = _QtCore.QPoint
    QDateTime = _QtCore.QDateTime
    QTimer = _QtCore.QTimer
    QEvent = _QtCore.QEvent
    QBuffer = _QtCore.QBuffer
    QIODevice = _QtCore.QIODevice
    QThread = _QtCore.QThread
    pyqtSignal = _QtCore.pyqtSignal
    QObject = _QtCore.QObject

    QIcon = _QtGui.QIcon
    QColor = _QtGui.QColor
    QImage = _QtGui.QImage
    QPixmap = _QtGui.QPixmap
    QPainter = _QtGui.QPainter
    QFont = _QtGui.QFont
    QKeySequence = _QtGui.QKeySequence
    QAction = _QtWidgets.QAction
    QDesktopServices = _QtGui.QDesktopServices

    QApplication = _QtWidgets.QApplication
    QMainWindow = _QtWidgets.QMainWindow
    QWidget = _QtWidgets.QWidget
    QDialog = _QtWidgets.QDialog
    QMenu = _QtWidgets.QMenu
    QFrame = _QtWidgets.QFrame
    QHBoxLayout = _QtWidgets.QHBoxLayout
    QVBoxLayout = _QtWidgets.QVBoxLayout
    QLabel = _QtWidgets.QLabel
    QLineEdit = _QtWidgets.QLineEdit
    QPushButton = _QtWidgets.QPushButton
    QSizePolicy = _QtWidgets.QSizePolicy
    QMessageBox = _QtWidgets.QMessageBox
    QFileDialog = _QtWidgets.QFileDialog
    QStatusBar = _QtWidgets.QStatusBar
    QTabBar = _QtWidgets.QTabBar
    QTabWidget = _QtWidgets.QTabWidget
    QToolBar = _QtWidgets.QToolBar
    QDockWidget = _QtWidgets.QDockWidget
    QListWidget = _QtWidgets.QListWidget
    QListWidgetItem = _QtWidgets.QListWidgetItem
    QCompleter = _QtWidgets.QCompleter
    QButtonGroup = _QtWidgets.QButtonGroup
    QCheckBox = _QtWidgets.QCheckBox
    QComboBox = _QtWidgets.QComboBox
    QFormLayout = _QtWidgets.QFormLayout
    QGroupBox = _QtWidgets.QGroupBox
    QHeaderView = _QtWidgets.QHeaderView
    QRadioButton = _QtWidgets.QRadioButton
    QScrollArea = _QtWidgets.QScrollArea
    QTableWidget = _QtWidgets.QTableWidget
    QTableWidgetItem = _QtWidgets.QTableWidgetItem
    QTextEdit = _QtWidgets.QTextEdit
    QProgressBar = _QtWidgets.QProgressBar
    QNetworkProxy = _QtNetwork.QNetworkProxy

    QWebEngineView = _QtWebEngineWidgets.QWebEngineView
    QWebEnginePage = _QtWebEngineWidgets.QWebEnginePage
    QWebEngineProfile = _QtWebEngineWidgets.QWebEngineProfile
    QWebEngineScript = _QtWebEngineWidgets.QWebEngineScript
    QWebEngineSettings = _QtWebEngineWidgets.QWebEngineSettings
    QWebEngineUrlRequestInterceptor = _QtWebEngineCore.QWebEngineUrlRequestInterceptor
    QWebEngineUrlRequestInfo = _QtWebEngineCore.QWebEngineUrlRequestInfo
    QWebEngineDownloadRequest = getattr(_QtWebEngineCore, "QWebEngineDownloadItem", getattr(_QtWebEngineWidgets, "QWebEngineDownloadItem", None))
