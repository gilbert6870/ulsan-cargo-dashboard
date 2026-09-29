@echo off
cd /d "%~dp0"
set LOGFILE=%~dp0logs\daily_update.log
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo === Daily Update Start: %DATE% %TIME% === >> "%LOGFILE%"

REM Python 경로 설정 (venv 우선)
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY=%~dp0.venv\Scripts\python.exe"
) else (
    set "PY=python"
)

REM Step 1: PLISM 최근 7일 증분 수집 (변동사항만 업데이트)
echo [INFO] fetch_prism_v31.py --days 7 시작 >> "%LOGFILE%"
"%PY%" "%~dp0fetch_prism_v31.py" --days 7 >> "%LOGFILE%" 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 수집 실패 >> "%LOGFILE%"
    exit /b 1
)

REM Step 2: Git commit and push
"%PY%" "%~dp0build_data.py" >> "%LOGFILE%" 2>&1
git -C "%~dp0" add data\monthly_*.csv data\index.json data\summary.json >> "%LOGFILE%" 2>&1
git -C "%~dp0" commit -m "data: daily cargo update %DATE%" >> "%LOGFILE%" 2>&1
git -C "%~dp0" push origin master >> "%LOGFILE%" 2>&1
if %errorlevel% neq 0 (
    echo [WARN] git push 실패 >> "%LOGFILE%"
) else (
    echo [OK] GitHub Pages 업데이트 완료 >> "%LOGFILE%"
)
echo === Daily Update End: %TIME% === >> "%LOGFILE%"
