@echo off
echo PLISM 매일 9시 자동 수집 - 작업 스케줄러 등록 중...

schtasks /create ^
  /tn "PLISM_Daily_Collect" ^
  /tr ""D:\[0]USER\Desktop\바이브코드\프로젝트\흥아라인 울산항 물동량 확인\daily_update.bat"" ^
  /sc DAILY ^
  /st 09:00 ^
  /ru "" ^
  /f

if %errorlevel% == 0 (
  echo.
  echo [성공] 매일 오전 9시 자동 수집 및 GitHub 업로드가 등록되었습니다.
  echo 작업 이름: PLISM_Daily_Collect
  echo 실행 파일: daily_update.bat
) else (
  echo.
  echo [실패] 관리자 권한으로 실행해주세요.
  echo 이 파일을 우클릭 -^> 관리자 권한으로 실행
)
pause
