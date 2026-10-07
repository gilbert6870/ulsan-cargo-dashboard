@echo off
cd /d "%~dp0"
if not exist "%~dp0logs" mkdir "%~dp0logs"
set "LOG=%~dp0logs\daily_update.log"
set "MARK=%~dp0logs\last_success.txt"
if exist "%~dp0.venv\Scripts\python.exe" (set "PY=%~dp0.venv\Scripts\python.exe") else (set "PY=python")

REM already done today? (skip unless "force")
if /i not "%~1"=="force" (
  "%PY%" -c "import datetime,sys,os;p=os.environ['MARK'];sys.exit(0 if os.path.exists(p) and open(p).read().strip()==datetime.date.today().isoformat() else 1)"
  if not errorlevel 1 exit /b 0
)

echo.>> "%LOG%"
echo ===== Daily update start %DATE% %TIME% =====>> "%LOG%"
echo [1/3] fetch last 7 days>> "%LOG%"
"%PY%" "%~dp0fetch_prism_v31.py" --days 7 >> "%LOG%" 2>&1
if errorlevel 1 (
  echo [ERROR] fetch failed - will retry next hour>> "%LOG%"
  exit /b 1
)

echo [2/3] build monthly files>> "%LOG%"
"%PY%" "%~dp0build_data.py" >> "%LOG%" 2>&1
if errorlevel 1 (
  echo [ERROR] build failed - will retry next hour>> "%LOG%"
  exit /b 1
)

echo [3/3] git push>> "%LOG%"
git -C "%~dp0." add data/monthly_*.csv data/index.json data/summary.json data/voyages.json data/sizes.json data/shippers.json >> "%LOG%" 2>&1
git -C "%~dp0." commit -m "data: daily update %DATE%" >> "%LOG%" 2>&1
git -C "%~dp0." push origin master >> "%LOG%" 2>&1
if errorlevel 1 (
  echo [WARN] git push failed - will retry next hour>> "%LOG%"
  exit /b 1
)
"%PY%" -c "import datetime,os;open(os.environ['MARK'],'w').write(datetime.date.today().isoformat())"
echo [OK] GitHub Pages updated>> "%LOG%"
echo ===== Daily update end %DATE% %TIME% =====>> "%LOG%"
exit /b 0
