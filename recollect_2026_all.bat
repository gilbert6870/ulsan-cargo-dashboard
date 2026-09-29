@echo off
cd /d "%~dp0"
if exist "%~dp0.venv\Scripts\python.exe" (set "PY=%~dp0.venv\Scripts\python.exe") else (set "PY=python")
echo [1/3] 2026 Jan-Sep re-fetch with port/FE fields...
"%PY%" fetch_prism_v31.py --date-from 20260101 --date-to 20260930
echo [2/3] Build monthly files...
"%PY%" build_data.py
echo [3/3] Push to GitHub...
git add data\monthly_*.csv data\index.json data\summary.json
git commit -m "data: 2026 re-fetch with port/FE fields"
git push origin master
echo Done!
pause
