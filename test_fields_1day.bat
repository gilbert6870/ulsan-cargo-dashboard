@echo off
cd /d "%~dp0"
echo PLISM field check - 1 day test fetch...
python fetch_prism_v31.py --date-from 20260925 --date-to 20260925
echo.
echo Done! Check logs\plism_fields_sample.json
pause
