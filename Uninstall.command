#!/bin/bash
# Uninstall.command — macOS double-click uninstaller

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

clear
echo ""
echo "  ================================================"
echo "    SearchPDF — Uninstaller"
echo "  ================================================"
echo ""
echo "  This will remove:"
echo "    - pip packages  (paddlepaddle, paddleocr, PyQt6, Pillow, pymupdf)"
echo "    - PaddleOCR model cache  (~/.paddleocr)"
echo "    - Desktop shortcut"
echo "    - Optionally: this project folder"
echo ""
read -rp "  Continue? (y/N): " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "  Aborted."
    read -rp "  Press Enter to exit..."
    exit 0
fi

# ── Uninstall pip packages ───────────────────────────
echo ""
echo "  [1/4] Uninstalling pip packages..."
python3 -m pip uninstall paddlepaddle paddleocr PyQt6 PyQt6-Qt6 PyQt6-sip Pillow pymupdf -y
echo "        Done."

# ── Remove model cache ──────────────────────────────
echo ""
echo "  [2/4] Removing PaddleOCR model cache..."
CACHE="$HOME/.paddleocr"
if [ -d "$CACHE" ]; then
    SIZE=$(du -sh "$CACHE" 2>/dev/null | cut -f1)
    echo "        Found: $CACHE  ($SIZE)"
    read -rp "        Delete? (y/N): " DEL_CACHE
    if [[ "$DEL_CACHE" == "y" || "$DEL_CACHE" == "Y" ]]; then
        rm -rf "$CACHE"
        echo "        Deleted."
    else
        echo "        Skipped."
    fi
else
    echo "        No cache found."
fi

# ── Remove Desktop shortcut ─────────────────────────
echo ""
echo "  [3/4] Removing Desktop shortcut..."
SHORTCUT="$HOME/Desktop/Launch SearchPDF.command"
if [ -f "$SHORTCUT" ]; then
    rm -f "$SHORTCUT"
    echo "        Deleted shortcut."
else
    echo "        No shortcut found."
fi

# ── Optionally delete project folder ────────────────
echo ""
echo "  [4/4] Delete project folder?"
echo "        $PROJECT_DIR"
read -rp "        Delete? (y/N): " DEL_PROJECT
if [[ "$DEL_PROJECT" == "y" || "$DEL_PROJECT" == "Y" ]]; then
    # Schedule deletion after script exits
    (sleep 1 && rm -rf "$PROJECT_DIR") &
    echo "        Scheduled for deletion."
else
    echo "        Skipped."
fi

echo ""
echo "  ================================================"
echo "    Uninstall complete."
echo "  ================================================"
echo ""
read -rp "  Press Enter to exit..."
