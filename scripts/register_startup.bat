@echo off
setlocal
cd /d "%~dp0\.."
set "PROJECT_DIR=%CD%"
set "VBS_LAUNCHER=%PROJECT_DIR%\Launch_JARVIS_Silent.vbs"
set "ICON_PATH=%PROJECT_DIR%\assets\jarvis_icon.ico"
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_FOLDER%\Personal JARVIS.lnk"

echo Configuring Personal JARVIS Autostart...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$wsh = New-Object -ComObject WScript.Shell; " ^
    "$s = $wsh.CreateShortcut('%SHORTCUT_PATH%'); " ^
    "$s.TargetPath = 'wscript.exe'; " ^
    "$s.Arguments = '\"%VBS_LAUNCHER%\"'; " ^
    "$s.WorkingDirectory = '%PROJECT_DIR%'; " ^
    "$s.Description = 'Personal JARVIS Autostart'; " ^
    "if (Test-Path '%ICON_PATH%') { $s.IconLocation = '%ICON_PATH%, 0' }; " ^
    "$s.Save(); " ^
    "Write-Host 'Autostart successfully registered in Windows Startup folder!' -ForegroundColor Green"

exit /b 0
