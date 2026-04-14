@echo off
REM build_windows.bat
REM Packages the app into a standalone Windows .exe
REM Run from the project directory: build_windows.bat

echo Installing PyInstaller...
pip install pyinstaller

echo Building SearchablePDFBuilder.exe...
pyinstaller ^
    --name "SearchablePDFBuilder" ^
    --windowed ^
    --onedir ^
    --hidden-import=paddleocr ^
    --hidden-import=paddle ^
    --hidden-import=fitz ^
    --hidden-import=PyQt6.QtWidgets ^
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui ^
    --collect-all paddleocr ^
    --collect-all paddle ^
    main.py

echo.
echo Done. Executable: dist\SearchablePDFBuilder\SearchablePDFBuilder.exe
pause
