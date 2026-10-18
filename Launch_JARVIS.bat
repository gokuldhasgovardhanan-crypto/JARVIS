@echo off
setlocal
cd /d "%~dp0"
title Personal JARVIS
echo Launching Personal JARVIS Assistant...

if not exist ".venv\Scripts\python.exe" (
    echo Error: Virtual environment .venv not found.
    echo Please run setup first.
    pause
    exit /b 1
)

start "" ".venv\Scripts\pythonw.exe" main.py
exit /b 0
