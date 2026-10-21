# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Collect all PyQt6 files (needed for WebEngine)
pyqt6_datas, pyqt6_binaries, pyqt6_hiddenimports = collect_all('PyQt6')

# Collect all cryptography files (needed for CryptoVault)
crypto_datas, crypto_binaries, crypto_hiddenimports = collect_all('cryptography')

# Lock Down Browser source datas
added_datas = [
    ('lockdown', 'lockdown'),
    ('icons', 'icons'),
    ('lockdown_logo.ico', '.'),
    ('lockdown_logo.png', '.'),
    ('lockdown_logo_transparent.png', '.'),
]

a = Analysis(
    ['browser.py'],
    pathex=['.'],
    binaries=pyqt6_binaries + crypto_binaries,
    datas=added_datas + pyqt6_datas + crypto_datas,
    hiddenimports=pyqt6_hiddenimports + crypto_hiddenimports + [
        'cryptography',
        'cryptography.exceptions',
        'cryptography.hazmat',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.primitives.hashes',
        'cryptography.hazmat.primitives.ciphers',
        'cryptography.hazmat.primitives.ciphers.aead',
        'cryptography.hazmat.primitives.kdf',
        'cryptography.hazmat.primitives.kdf.pbkdf2',
        'cryptography.hazmat.backends',
        'cryptography.hazmat.backends.openssl',
        'lockdown',
        'lockdown.config',
        'lockdown.theme',
        'lockdown.homepage',
        'lockdown.home_server',
        'lockdown.blocker',
        'lockdown.history_manager',
        'lockdown.download_manager',
        'lockdown.downloads_page',
        'lockdown.extensions_page',
        'lockdown.extension_manager',
        'lockdown.extensions_library',
        'lockdown.settings_page',
        'lockdown.gemini_service',
        'lockdown.crypto_vault',
        'lockdown.drive_sync',
        'lockdown.vpn_service',
        'lockdown.suggestions',
        'lockdown.icons',
        'lockdown.qt_compat',
        'lockdown.ui',
        'flask',
        'werkzeug',
        'httpx',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.QtWebEngineWidgets'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LockDownBrowser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='lockdown_logo.ico',
    version='file_version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LockDownBrowser',
)
