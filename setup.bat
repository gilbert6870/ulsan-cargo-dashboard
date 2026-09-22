@echo off
echo ============================================
echo 흥아라인 울산항 물동량 시스템 설치
echo ============================================
echo.

echo [1/3] Python 패키지 설치 중...
pip install -r requirements.txt
if errorlevel 1 goto error

echo [2/3] Playwright 브라우저 설치 중...
playwright install chromium
if errorlevel 1 goto error

echo [3/3] .env 파일 확인...
if not exist .env (
    copy .env.example .env
    echo .env 파일이 생성되었습니다.
    echo 메모장으로 열어서 아이디와 비번을 입력하세요!
    notepad .env
) else (
    echo .env 파일이 이미 존재합니다.
)

echo.
echo ============================================
echo 설치 완료!
echo 이제 run_fetch.bat을 실행하여 데이터를 수집하세요.
echo ============================================
pause
goto end

:error
echo.
echo 오류가 발생했습니다. Python이 설치되어 있는지 확인하세요.
echo https://python.org 에서 Python 3.10 이상을 설치하세요.
pause

:end
