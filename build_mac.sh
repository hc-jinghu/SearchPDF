#!/bin/bash
# build_mac.sh
# Packages the app into a standalone macOS .app bundle.
# Run from the project directory: bash build_mac.sh

set -e

echo "Installing PyInstaller..."
pip install pyinstaller

echo "Building SearchablePDFBuilder.app..."
pyinstaller \
    --name "SearchablePDFBuilder" \
    --windowed \
    --onedir \
    --hidden-import=paddleocr \
    --hidden-import=paddle \
    --hidden-import=fitz \
    --hidden-import=PyQt6.QtWidgets \
    --hidden-import=PyQt6.QtCore \
    --hidden-import=PyQt6.QtGui \
    --collect-all paddleocr \
    --collect-all paddle \
    main.py

echo ""
echo "Done. App bundle: dist/SearchablePDFBuilder.app"
