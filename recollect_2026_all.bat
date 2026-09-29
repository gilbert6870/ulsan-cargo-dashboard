@echo off
cd /d "%~dp0"
if not exist logs mkdir logs
if exist "%~dp0.venv\Scripts\python.exe" (set "PY=%~dp0.venv\Scripts\python.exe") else (set "PY=python")
set LOG=%~dp0logs\recollect.log
echo ===== recollect start %DATE% %TIME% ===== >> "%LOG%"
echo [1/9] fetch 20260101 - 20260131 ...
echo --- 20260101-20260131 --- >> "%LOG%"
"%PY%" fetch_prism_v31.py --date-from 20260101 --date-to 20260131 >> "%LOG%" 2>&1
if errorlevel 1 (echo     FAILED - see logs\recollect.log) else (echo     OK)
echo [2/9] fetch 20260201 - 20260228 ...
echo --- 20260201-20260228 --- >> "%LOG%"
"%PY%" fetch_prism_v31.py --date-from 20260201 --date-to 20260228 >> "%LOG%" 2>&1
if errorlevel 1 (echo     FAILED - see logs\recollect.log) else (echo     OK)
echo [3/9] fetch 20260301 - 20260331 ...
echo --- 20260301-20260331 --- >> "%LOG%"
"%PY%" fetch_prism_v31.py --date-from 20260301 --date-to 20260331 >> "%LOG%" 2>&1
if errorlevel 1 (echo     FAILED - see logs\recollect.log) else (echo     OK)
echo [4/9] fetch 20260401 - 20260430 ...
echo --- 20260401-20260430 --- >> "%LOG%"
"%PY%" fetch_prism_v31.py --date-from 20260401 --date-to 20260430 >> "%LOG%" 2>&1
if errorlevel 1 (echo     FAILED - see logs\recollect.log) else (echo     OK)
echo [5/9] fetch 20260501 - 20260531 ...
echo --- 20260501-20260531 --- >> "%LOG%"
"%PY%" fetch_prism_v31.py --date-from 20260501 --date-to 20260531 >> "%LOG%" 2>&1
if errorlevel 1 (echo     FAILED - see logs\recollect.log) else (echo     OK)
echo [6/9] fetch 20260601 - 20260630 ...
echo --- 20260601-20260630 --- >> "%LOG%"
"%PY%" fetch_prism_v31.py --date-from 20260601 --date-to 20260630 >> "%LOG%" 2>&1
if errorlevel 1 (echo     FAILED - see logs\recollect.log) else (echo     OK)
echo [7/9] fetch 20260701 - 20260731 ...
echo --- 20260701-20260731 --- >> "%LOG%"
"%PY%" fetch_prism_v31.py --date-from 20260701 --date-to 20260731 >> "%LOG%" 2>&1
if errorlevel 1 (echo     FAILED - see logs\recollect.log) else (echo     OK)
echo [8/9] fetch 20260801 - 20260831 ...
echo --- 20260801-20260831 --- >> "%LOG%"
"%PY%" fetch_prism_v31.py --date-from 20260801 --date-to 20260831 >> "%LOG%" 2>&1
if errorlevel 1 (echo     FAILED - see logs\recollect.log) else (echo     OK)
echo [9/9] fetch 20260901 - 20260930 ...
echo --- 20260901-20260930 --- >> "%LOG%"
"%PY%" fetch_prism_v31.py --date-from 20260901 --date-to 20260930 >> "%LOG%" 2>&1
if errorlevel 1 (echo     FAILED - see logs\recollect.log) else (echo     OK)
echo [build] monthly files ...
"%PY%" build_data.py >> "%LOG%" 2>&1
echo [git] push ...
git add data\monthly_*.csv data\index.json data\summary.json >> "%LOG%" 2>&1
git commit -m "data: 2026 re-fetch with customs/FE/transship fields" >> "%LOG%" 2>&1
git push origin master >> "%LOG%" 2>&1
if errorlevel 1 (echo     push FAILED - see logs\recollect.log) else (echo     push OK)
echo Done!
pause
