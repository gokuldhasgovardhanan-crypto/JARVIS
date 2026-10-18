$projectDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$vbsLauncher = Join-Path $projectDir "Launch_JARVIS_Silent.vbs"
$iconPath = Join-Path $projectDir "assets\jarvis_icon.ico"
$wsh = New-Object -ComObject WScript.Shell

# 1. Desktop Shortcut
$desktopPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
$desktopShortcutPath = Join-Path $desktopPath "Personal JARVIS.lnk"

$shortcut = $wsh.CreateShortcut($desktopShortcutPath)
$shortcut.TargetPath = "wscript.exe"
$shortcut.Arguments = "`"$vbsLauncher`""
$shortcut.WorkingDirectory = $projectDir
$shortcut.Description = "Personal JARVIS Multilingual AI Desktop Assistant"
if (Test-Path $iconPath) {
    $shortcut.IconLocation = "$iconPath, 0"
}
$shortcut.Save()
Write-Host "Created Desktop Shortcut at: $desktopShortcutPath" -ForegroundColor Cyan

# 2. Start Menu Shortcut
$startMenuPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Programs)
$startShortcutPath = Join-Path $startMenuPath "Personal JARVIS.lnk"

$startShortcut = $wsh.CreateShortcut($startShortcutPath)
$startShortcut.TargetPath = "wscript.exe"
$startShortcut.Arguments = "`"$vbsLauncher`""
$startShortcut.WorkingDirectory = $projectDir
$startShortcut.Description = "Personal JARVIS Multilingual AI Desktop Assistant"
if (Test-Path $iconPath) {
    $startShortcut.IconLocation = "$iconPath, 0"
}
$startShortcut.Save()
Write-Host "Created Start Menu Shortcut at: $startShortcutPath" -ForegroundColor Cyan
