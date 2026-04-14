@echo off
title SearchPDF - Installer
color 0A
echo.
echo  ================================================
echo    SearchPDF - Installer
echo  ================================================
echo.

REM ── Check for Python ──────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  Python was not found on this machine.
    echo  Opening the Python download page in your browser...
    echo.
    start https://www.python.org/downloads/
    echo  Please install Python 3.8 or higher, making sure to tick
    echo  "Add Python to PATH" during setup, then run this installer again.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version') do set PYVER=%%v
echo  Found: %PYVER%
echo.

REM ── Run install.py ────────────────────────────────
echo  Installing packages (this may take a few minutes)...
echo.
cd /d "%~dp0"
python install.py
if errorlevel 1 (
    echo.
    echo  Something went wrong during installation.
    echo  Check the output above for details.
    pause
    exit /b 1
)

REM ── Create Desktop shortcut (.bat) ────────────────
set PROJECT_DIR=%~dp0
set SHORTCUT=%USERPROFILE%\Desktop\SearchPDF.bat

echo @echo off                                          > "%SHORTCUT%"
echo cd /d "%PROJECT_DIR%"                             >> "%SHORTCUT%"
echo python main.py                                    >> "%SHORTCUT%"

echo.
echo  ================================================
echo    Installation complete!
echo.
echo    A shortcut has been placed on your Desktop:
echo    "SearchPDF"
echo  ================================================
echo.
pause
