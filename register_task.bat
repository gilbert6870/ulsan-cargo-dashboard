@echo off
echo Register daily 09:00 update task...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0register_task.ps1"
echo.
echo Run the update once now to test? (Y/N)
set /p ans=
if /i "%ans%"=="Y" (
  echo Running daily_update.bat ... please wait
  call "%~dp0daily_update.bat" force
  echo Done. Result is in logs\daily_update.log
)
pause
