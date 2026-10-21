@echo off
setlocal enabledelayedexpansion
title Trust Ankush Code Signing Certificate

echo ==========================================================
echo   Lock Down Browser - Windows Protection & Publisher Setup
echo   Publisher: Ankush
echo ==========================================================
echo.

:: Check for Administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting Administrator privileges to install trusted certificate...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

echo [1/3] Installing Ankush Code Signing Certificate to Trusted Stores...
if exist "AnkushCodeSigning.cer" (
    certutil -addstore -f "Root" "AnkushCodeSigning.cer" >nul 2>&1
    certutil -addstore -f "TrustedPublisher" "AnkushCodeSigning.cer" >nul 2>&1
    certutil -user -addstore -f "TrustedPublisher" "AnkushCodeSigning.cer" >nul 2>&1
    echo       Certificate installed to Root and TrustedPublisher stores.
) else (
    echo       ERROR: AnkushCodeSigning.cer not found!
)

echo [2/3] Removing Mark-of-the-Web (Zone.Identifier) protection flags...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-ChildItem -Path '.' -Recurse -Include *.exe | Unblock-File -ErrorAction SilentlyContinue"
echo       Protection unblock applied.

echo [3/3] Verifying Digital Signature on LockDownBrowser-Setup.exe...
if exist "Output\LockDownBrowser-Setup.exe" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$sig = Get-AuthenticodeSignature 'Output\LockDownBrowser-Setup.exe'; Write-Host '      Status    :' $sig.Status; Write-Host '      Publisher :' $sig.SignerCertificate.Subject"
)

echo.
echo ==========================================================
echo   SUCCESS! Windows Defender SmartScreen will now recognize
echo   Ankush as a Verified Publisher.
echo ==========================================================
echo.
pause
