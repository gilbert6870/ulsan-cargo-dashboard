' Runs daily_update.bat with NO visible window (so it can't be closed or paused by accident)
Set sh = CreateObject("WScript.Shell")
d = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
sh.CurrentDirectory = d
rc = sh.Run("cmd.exe /c """ & d & "daily_update.bat""", 0, True)
WScript.Quit rc
