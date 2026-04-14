#!/bin/bash
# Install.command — macOS double-click installer
# First time: right-click → Open With → Terminal
# After install: double-click works directly

# Move to the folder this script lives in
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# Make all .command files executable so future runs are double-click
chmod +x "$PROJECT_DIR"/*.command

clear
echo ""
echo "  ================================================"
echo "    SearchPDF — Installer"
echo "  ================================================"
echo ""

# ── Check for Python 3 ──────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "  Python 3 was not found on this machine."
    echo "  Opening the Python download page in your browser..."
    open "https://www.python.org/downloads/"
    echo ""
    echo "  Please install Python 3.8 or higher, then run this installer again."
    echo ""
    read -rp "  Press Enter to exit..."
    exit 1
fi

PYVER=$(python3 --version 2>&1)
echo "  Found: $PYVER"
echo ""

# ── Run install.py ──────────────────────────────────
echo "  Installing packages (this may take a few minutes)..."
echo "  (PaddleOCR models, ~100 MB, will download on first use)"
echo ""
python3 "$PROJECT_DIR/install.py"

if [ $? -ne 0 ]; then
    echo ""
    echo "  Something went wrong. Check the output above."
    read -rp "  Press Enter to exit..."
    exit 1
fi

# ── Create Desktop shortcut (.command) ──────────────
SHORTCUT="$HOME/Desktop/Launch SearchPDF.command"

cat > "$SHORTCUT" << SHORTCUT_CONTENT
#!/bin/bash
cd "$PROJECT_DIR"
python3 main.py
SHORTCUT_CONTENT

chmod +x "$SHORTCUT"

echo ""
echo "  ================================================"
echo "    Installation complete!"
echo ""
echo "    A shortcut has been placed on your Desktop:"
echo "    'Launch SearchPDF'"
echo "  ================================================"
echo ""
read -rp "  Press Enter to exit..."
