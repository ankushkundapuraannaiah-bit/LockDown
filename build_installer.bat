@echo off
setlocal
title Build and Sign Lock Down Browser
echo ==========================================================
echo   Building and Signing Lock Down Browser
echo   Publisher: Ankush
echo ==========================================================
echo.

cd /d "%~dp0"

:: 1. Compile PyInstaller distribution
echo [1/4] Building with PyInstaller...
python -m PyInstaller --noconfirm LockDownBrowser.spec
if %errorlevel% neq 0 (
    echo ERROR: PyInstaller build failed!
    pause
    exit /b %errorlevel%
)

:: 2. Sign PyInstaller binary
echo.
echo [2/4] Signing dist\LockDownBrowser\LockDownBrowser.exe...
powershell -NoProfile -ExecutionPolicy Bypass -File .\sign_binaries.ps1 -FilesToSign "dist\LockDownBrowser\LockDownBrowser.exe"
if %errorlevel% neq 0 (
    echo Warning: Signing dist binary encountered an issue.
)

:: 3. Compile Inno Setup Installer
echo.
echo [3/4] Compiling Inno Setup Installer...
set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"

if exist "%ISCC%" (
    "%ISCC%" setup.iss
    if %errorlevel% neq 0 (
        echo ERROR: Inno Setup compilation failed!
        pause
        exit /b %errorlevel%
    )
) else (
    echo ERROR: Inno Setup compiler (ISCC.exe) not found!
    pause
    exit /b 1
)

:: 4. Sign the Installer
echo.
echo [4/4] Signing Output\LockDownBrowser-Setup.exe...
powershell -NoProfile -ExecutionPolicy Bypass -File .\sign_binaries.ps1 -FilesToSign "Output\LockDownBrowser-Setup.exe"

echo.
echo ==========================================================
echo   Build and Signature Complete!
echo   Publisher : Ankush
echo   Location  : Output\LockDownBrowser-Setup.exe
echo ==========================================================
echo.
pause
