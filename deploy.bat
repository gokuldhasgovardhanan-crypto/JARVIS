@echo off
setlocal
cd /d "%~dp0"
echo ==============================================================
echo       PERSONAL JARVIS — WINDOWS 11 DEPLOYMENT SYSTEM
echo ==============================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment (.venv) not found.
    pause
    exit /b 1
)

echo Installing Windows Desktop and Start Menu Shortcuts...
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\create_shortcuts.ps1"

echo.
echo ==============================================================
echo  Deployment Successful!
echo  • Desktop Shortcut: Personal JARVIS.lnk
echo  • Start Menu: Personal JARVIS.lnk
echo  • One-Click Batch: Launch_JARVIS.bat
echo  • Silent Background VBS: Launch_JARVIS_Silent.vbs
echo ==============================================================
echo.
exit /b 0
