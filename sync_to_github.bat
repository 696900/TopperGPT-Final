@echo off
setlocal
echo ========================================================
echo  Syncing TopperGPT workspace to GitHub (origin/main)
echo ========================================================
echo.

git status --short
echo.

set /p MSG="Enter commit message (press Enter for default): "
if "%MSG%"=="" (
    set MSG=Update workspace files: %date% %time%
)

echo.
echo [1/3] Staging changes...
git add -A

echo [2/3] Committing changes with message: "%MSG%"
git diff-index --quiet HEAD || git commit -m "%MSG%"

echo [3/3] Pushing changes to GitHub main branch...
git push origin main

echo.
if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] Changes successfully synced to GitHub!
) else (
    echo [ERROR] Push encountered an issue. Please review the output above.
)

echo.
pause
