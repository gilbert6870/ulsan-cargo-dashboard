@echo off
echo ============================================
echo 프리즘 물동량 데이터 수집 시작
echo ============================================
echo.
echo .env 파일의 로그인 정보로 접속합니다...
python fetch_prism.py
echo.
echo 수집 완료! data 폴더를 확인하세요.
pause
