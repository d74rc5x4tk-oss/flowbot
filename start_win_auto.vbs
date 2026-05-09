Dim WshShell, sDir
sDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """" & sDir & "\.venv\Scripts\pythonw.exe"" """ & sDir & "\main.py""", 0, False
