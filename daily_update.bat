@echo off
cd /d "%~dp0"
if not exist "%~dp0logs" mkdir "%~dp0logs"
set "LOG=%~dp0logs\daily_update.log"
echo.>> "%LOG%"
echo ===== Daily update start %DATE% %TIME% =====>> "%LOG%"
if exist "%~dp0.venv\Scripts\python.exe" (set "PY=%~dp0.venv\Scripts\python.exe") else (set "PY=python")

echo [1/3] fetch last 7 days>> "%LOG%"
"%PY%" "%~dp0fetch_prism_v31.py" --days 7 >> "%LOG%" 2>&1
if errorlevel 1 (
  echo [ERROR] fetch failed - skip build/push>> "%LOG%"
  exit /b 1
)

echo [2/3] build monthly files>> "%LOG%"
"%PY%" "%~dp0build_data.py" >> "%LOG%" 2>&1
if errorlevel 1 (
  echo [ERROR] build failed - skip push>> "%LOG%"
  exit /b 1
)

echo [3/3] git push>> "%LOG%"
git -C "%~dp0." add data/monthly_*.csv data/index.json data/summary.json >> "%LOG%" 2>&1
git -C "%~dp0." commit -m "data: daily update %DATE%" >> "%LOG%" 2>&1
git -C "%~dp0." push origin master >> "%LOG%" 2>&1
if errorlevel 1 (echo [WARN] git push failed>> "%LOG%") else (echo [OK] GitHub Pages updated>> "%LOG%")
echo ===== Daily update end %DATE% %TIME% =====>> "%LOG%"
exit /b 0
