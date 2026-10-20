"""Lock Down Browser Master Theme.
Modern Yellow & White theme — clean, warm, sunshine aesthetic.
High contrast dark text on yellow and white surfaces with amber accents.
"""

from lockdown.config import (
    COLOR_BLUE_BASE,
    COLOR_BLUE_BORDER,
    COLOR_BLUE_DARK,
    COLOR_BLUE_DARKEST,
    COLOR_BLUE_HIGHLIGHT,
    COLOR_BLUE_SURFACE,
    COLOR_CORAL_HOVER,
    COLOR_CORAL_PRESSED,
    COLOR_CORAL_PRIMARY,
    COLOR_TEXT_DARK,
    COLOR_TEXT_MED,
    COLOR_WHITE,
    COLOR_YELLOW_ACCENT,
    COLOR_YELLOW_BRIGHT,
    COLOR_YELLOW_SOFT,
)

APPLICATION_STYLESHEET = f"""
/* =========================================================================
   LOCK DOWN BROWSER MASTER THEME
   Palette: Yellow & White — Modern Sunshine
   ========================================================================= */

QMainWindow {{
    background-color: {COLOR_BLUE_DARKEST};
    color: {COLOR_TEXT_DARK};
}}

QWidget {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: {COLOR_TEXT_DARK};
}}

/* Top Navigation Toolbar */
QToolBar#navigationToolbar {{
    background-color: {COLOR_BLUE_DARK};
    border: none;
    border-bottom: 2px solid {COLOR_YELLOW_ACCENT};
    spacing: 8px;
    padding: 6px 14px;
}}

QToolButton {{
    background-color: {COLOR_WHITE};
    border: 1.5px solid {COLOR_BLUE_BORDER};
    border-radius: 8px;
    color: {COLOR_TEXT_DARK};
    padding: 6px 10px;
    font-size: 13px;
    font-weight: 600;
}}

QToolButton:hover {{
    background-color: {COLOR_BLUE_HIGHLIGHT};
    border-color: {COLOR_CORAL_PRIMARY};
    color: {COLOR_TEXT_DARK};
}}

QToolButton:pressed {{
    background-color: {COLOR_YELLOW_ACCENT};
    border-color: {COLOR_CORAL_PRESSED};
    color: {COLOR_TEXT_DARK};
}}

QToolButton:checked {{
    background-color: {COLOR_BLUE_SURFACE};
    border: 2px solid {COLOR_CORAL_PRIMARY};
    color: {COLOR_CORAL_PRIMARY};
}}

/* Pill-Shaped Integrated Omnibox */
QFrame#omniboxContainer {{
    background-color: {COLOR_WHITE};
    border: 2px solid {COLOR_YELLOW_ACCENT};
    border-radius: 20px;
    padding: 1px 6px;
}}

QFrame#omniboxContainer:focus-within {{
    border: 2px solid {COLOR_CORAL_PRIMARY};
    background-color: {COLOR_WHITE};
}}

QLineEdit#omniboxInput {{
    background: transparent;
    border: none;
    color: {COLOR_TEXT_DARK};
    font-size: 13.5px;
    font-weight: 500;
    selection-background-color: {COLOR_YELLOW_BRIGHT};
    selection-color: {COLOR_TEXT_DARK};
}}

QComboBox {{
    background-color: {COLOR_WHITE};
    border: 1.5px solid {COLOR_BLUE_BORDER};
    border-radius: 10px;
    color: {COLOR_TEXT_DARK};
    padding: 5px 12px;
    font-size: 12px;
    font-weight: 600;
}}

QComboBox:hover {{
    border-color: {COLOR_CORAL_PRIMARY};
}}

QComboBox::drop-down {{
    border: none;
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLOR_WHITE};
    border: 1.5px solid {COLOR_BLUE_BORDER};
    border-radius: 8px;
    color: {COLOR_TEXT_DARK};
    selection-background-color: {COLOR_BLUE_SURFACE};
    selection-color: {COLOR_TEXT_DARK};
    outline: none;
    padding: 4px;
}}

/* Primary & Action Buttons */
QPushButton {{
    background-color: {COLOR_WHITE};
    border: 1.5px solid {COLOR_BLUE_BORDER};
    border-radius: 8px;
    color: {COLOR_TEXT_DARK};
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: {COLOR_BLUE_HIGHLIGHT};
    border-color: {COLOR_CORAL_PRIMARY};
    color: {COLOR_TEXT_DARK};
}}

QPushButton:pressed {{
    background-color: {COLOR_YELLOW_ACCENT};
}}

QPushButton#primaryBtn {{
    background-color: {COLOR_CORAL_PRIMARY};
    color: #FFFFFF;
    border: 1.5px solid {COLOR_CORAL_HOVER};
}}

QPushButton#primaryBtn:hover {{
    background-color: {COLOR_CORAL_HOVER};
}}

QPushButton#primaryBtn:pressed {{
    background-color: {COLOR_CORAL_PRESSED};
}}

/* Tab Widget */
QTabWidget::pane {{
    border: none;
    background-color: {COLOR_BLUE_DARKEST};
}}

QTabBar {{
    background-color: {COLOR_BLUE_DARK};
}}

QTabBar::tab {{
    background-color: {COLOR_BLUE_SURFACE};
    border: 1.5px solid {COLOR_BLUE_BORDER};
    border-bottom: none;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    color: {COLOR_TEXT_MED};
    min-width: 140px;
    max-width: 230px;
    padding: 8px 14px;
    margin-right: 4px;
    font-size: 12.5px;
    font-weight: 600;
}}

QTabBar::tab:selected {{
    background-color: {COLOR_WHITE};
    color: {COLOR_TEXT_DARK};
    border: 1.5px solid {COLOR_YELLOW_ACCENT};
    border-bottom: 2px solid {COLOR_WHITE};
    border-top: 3px solid {COLOR_CORAL_PRIMARY};
    font-weight: 700;
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLOR_BLUE_HIGHLIGHT};
    color: {COLOR_TEXT_DARK};
}}

QTabBar::close-button {{
    image: url(icons/close.svg);
    subcontrol-position: right;
    margin-right: 4px;
    border-radius: 4px;
}}

QTabBar::close-button:hover {{
    background-color: rgba(230, 115, 0, 0.25);
}}

/* Sidebar Dock */
QDockWidget#sidebarDock {{
    background-color: {COLOR_BLUE_DARKEST};
    color: {COLOR_TEXT_DARK};
    border-right: 2px solid {COLOR_YELLOW_ACCENT};
}}

QDockWidget::title {{
    background-color: {COLOR_BLUE_DARK};
    color: {COLOR_TEXT_DARK};
    padding: 9px 12px;
    text-align: left;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1px;
    border-bottom: 1.5px solid {COLOR_YELLOW_ACCENT};
}}

/* Lists & Trees */
QListWidget {{
    background-color: {COLOR_WHITE};
    border: 1.5px solid {COLOR_BLUE_BORDER};
    border-radius: 10px;
    color: {COLOR_TEXT_DARK};
    outline: none;
    padding: 4px;
}}

QListWidget::item {{
    border-radius: 8px;
    padding: 8px 12px;
    margin: 2px 0px;
    font-size: 13px;
    color: {COLOR_TEXT_DARK};
}}

QListWidget::item:selected {{
    background-color: {COLOR_BLUE_SURFACE};
    border-left: 3.5px solid {COLOR_CORAL_PRIMARY};
    color: {COLOR_TEXT_DARK};
    font-weight: 700;
}}

QListWidget::item:hover:!selected {{
    background-color: {COLOR_BLUE_HIGHLIGHT};
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: {COLOR_BLUE_DARKEST};
    width: 9px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {COLOR_YELLOW_ACCENT};
    min-height: 24px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLOR_CORAL_PRIMARY};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* Status Bar */
QStatusBar {{
    background-color: {COLOR_BLUE_DARK};
    color: {COLOR_TEXT_MED};
    border-top: 2px solid {COLOR_YELLOW_ACCENT};
    font-size: 12px;
    font-weight: 600;
    padding: 4px 12px;
}}

/* Dialogs & Menus */
QDialog {{
    background-color: {COLOR_WHITE};
    color: {COLOR_TEXT_DARK};
    border: 2px solid {COLOR_YELLOW_ACCENT};
}}

QMenu {{
    background-color: {COLOR_WHITE};
    border: 1.5px solid {COLOR_YELLOW_ACCENT};
    border-radius: 10px;
    color: {COLOR_TEXT_DARK};
    padding: 6px;
}}

QMenu::item {{
    padding: 7px 22px;
    border-radius: 6px;
    color: {COLOR_TEXT_DARK};
    font-size: 13px;
}}

QMenu::item:selected {{
    background-color: {COLOR_BLUE_SURFACE};
    color: {COLOR_CORAL_PRIMARY};
    font-weight: 600;
}}

QMenu::separator {{
    height: 1.5px;
    background-color: {COLOR_YELLOW_ACCENT};
    margin: 4px 8px;
}}

/* Text Edits & Tables */
QTextEdit, QPlainTextEdit, QTableWidget {{
    background-color: {COLOR_WHITE};
    border: 1.5px solid {COLOR_BLUE_BORDER};
    border-radius: 8px;
    color: {COLOR_TEXT_DARK};
    padding: 8px;
}}

QHeaderView::section {{
    background-color: {COLOR_BLUE_DARK};
    color: {COLOR_TEXT_DARK};
    border: none;
    border-bottom: 2px solid {COLOR_YELLOW_ACCENT};
    padding: 7px 10px;
    font-weight: 700;
}}

/* Labels */
QLabel {{
    color: {COLOR_TEXT_DARK};
    background: transparent;
}}

/* Group Boxes */
QGroupBox {{
    border: 1.5px solid {COLOR_YELLOW_ACCENT};
    border-radius: 10px;
    margin-top: 10px;
    font-weight: 700;
    color: {COLOR_TEXT_DARK};
    padding-top: 10px;
    background-color: {COLOR_WHITE};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    color: {COLOR_CORAL_PRIMARY};
}}

/* Check Boxes & Radio Buttons */
QCheckBox, QRadioButton {{
    color: {COLOR_TEXT_DARK};
    spacing: 7px;
    font-weight: 500;
}}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background-color: {COLOR_YELLOW_ACCENT};
    border: 2px solid {COLOR_CORAL_PRIMARY};
}}

/* Line Edits (generic) */
QLineEdit {{
    background-color: {COLOR_WHITE};
    border: 1.5px solid {COLOR_BLUE_BORDER};
    border-radius: 8px;
    color: {COLOR_TEXT_DARK};
    padding: 7px 10px;
    font-size: 13px;
}}

QLineEdit:focus {{
    border-color: {COLOR_CORAL_PRIMARY};
}}

/* Spin Boxes */
QSpinBox, QDoubleSpinBox {{
    background-color: {COLOR_WHITE};
    border: 1.5px solid {COLOR_BLUE_BORDER};
    border-radius: 8px;
    color: {COLOR_TEXT_DARK};
    padding: 5px 8px;
}}

/* Progress Bar */
QProgressBar {{
    background-color: {COLOR_BLUE_SURFACE};
    border: 1.5px solid {COLOR_BLUE_BORDER};
    border-radius: 6px;
    text-align: center;
    color: {COLOR_TEXT_DARK};
    font-size: 11px;
    font-weight: 700;
}}

QProgressBar::chunk {{
    background-color: {COLOR_YELLOW_ACCENT};
    border-radius: 5px;
}}

/* Tool Tips */
QToolTip {{
    background-color: {COLOR_TEXT_DARK};
    color: #FFFFFF;
    border: 1.5px solid {COLOR_YELLOW_ACCENT};
    border-radius: 6px;
    padding: 5px 9px;
    font-size: 12px;
}}
"""
