@echo off
echo ============================================
echo [Heungaline] Ulsan Port Dashboard - Git Setup
echo ============================================
cd /d "%~dp0"

REM Remove lock file if it exists
if exist ".git\index.lock" (
    del /f /q ".git\index.lock"
    echo index.lock removed.
)

REM Git user config
git config user.email "jhopark@heungaline.com"
git config user.name "Glibert Park"

REM Stage all project files (not .env)
git add index.html README.md .gitignore .env.example CLAUDE.md
git add requirements.txt setup.bat run_fetch.bat run_watch.bat git_setup.bat
git add fetch_prism.py

REM Commit
git commit -m "feat: PLISM 3.0 export+import integration and dashboard update"

echo.
echo ============================================
echo Commit done! Next: connect GitHub
echo.
echo   git remote add origin https://github.com/[USERNAME]/ulsan-cargo.git
echo   git push -u origin master
echo.
echo Then enable GitHub Pages:
echo   Settings ^> Pages ^> Source: master branch
echo ============================================
pause
