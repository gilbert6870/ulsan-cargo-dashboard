@echo off
echo ============================================
echo 프리즘 물동량 자동 수집 (30분마다)
echo ============================================
echo.
echo 종료하려면 이 창을 닫거나 Ctrl+C를 누르세요.
python fetch_prism.py --watch
pause
