@echo off
title Lock Down Browser
echo Starting Lock Down Browser...
python browser.py
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Could not start Lock Down Browser.
    echo Make sure Python and dependencies are installed:
    echo   pip install -r requirements.txt
    pause
)
