Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonwPath = currentDir & "\.venv\Scripts\pythonw.exe"
mainScript = currentDir & "\main.py"

WshShell.CurrentDirectory = currentDir
WshShell.Run """" & pythonwPath & """ """ & mainScript & """", 0, False
Set WshShell = Nothing
Set fso = Nothing
