@echo off
title SearchPDF - Uninstaller
color 0C
echo.
echo  ================================================
echo    SearchPDF - Uninstaller
echo  ================================================
echo.
echo  This will remove:
echo    - pip packages  (paddlepaddle, paddleocr, PyQt6, Pillow, pymupdf)
echo    - PaddleOCR model cache  (%USERPROFILE%\.paddleocr)
echo    - Desktop shortcut
echo    - Optionally: this project folder
echo.
set /p CONFIRM= Continue? (y/N):
if /i not "%CONFIRM%"=="y" (
    echo  Aborted.
    pause
    exit /b 0
)

REM ── Uninstall packages ────────────────────────────
echo.
echo  [1/4] Uninstalling pip packages...
python -m pip uninstall paddlepaddle paddleocr PyQt6 PyQt6-Qt6 PyQt6-sip Pillow pymupdf -y
echo        Done.

REM ── Remove model cache ────────────────────────────
echo.
echo  [2/4] Removing PaddleOCR model cache...
if exist "%USERPROFILE%\.paddleocr" (
    rmdir /s /q "%USERPROFILE%\.paddleocr"
    echo        Deleted: %USERPROFILE%\.paddleocr
) else (
    echo        No cache found.
)

REM ── Remove Desktop shortcut ───────────────────────
echo.
echo  [3/4] Removing Desktop shortcut...
if exist "%USERPROFILE%\Desktop\SearchPDF.bat" (
    del "%USERPROFILE%\Desktop\SearchPDF.bat"
    echo        Deleted shortcut.
) else (
    echo        No shortcut found.
)

REM ── Optionally delete project folder ──────────────
echo.
echo  [4/4] Delete project folder?
echo        %~dp0
set /p DEL_PROJECT= Delete project folder? (y/N):
if /i "%DEL_PROJECT%"=="y" (
    echo        Scheduling deletion...
    REM Use a delayed cmd so this script can exit before its own folder is deleted
    start "" /b cmd /c "ping 127.0.0.1 -n 3 >nul && rmdir /s /q \"%~dp0\""
    echo        Scheduled.
) else (
    echo        Skipped.
)

echo.
echo  ================================================
echo    Uninstall complete.
echo  ================================================
echo.
pause
