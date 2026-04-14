#!/usr/bin/env python3
"""
OS-aware installer for SearchPDF.
Detects your operating system and installs the correct packages.

Usage:
    python install.py
"""

import sys
import subprocess
import platform


def run(cmd, desc=""):
    label = desc if desc else " ".join(cmd)
    print(f"  -> {label}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"     [WARN] exited with code {result.returncode}")
    return result.returncode == 0


def check_python():
    major, minor = sys.version_info[:2]
    print(f"Python {major}.{minor} detected")
    if major < 3 or (major == 3 and minor < 8):
        print("ERROR: Python 3.8 or higher is required.")
        sys.exit(1)


def upgrade_pip():
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], "Upgrading pip")


def install_packages(os_name, arch):
    # Packages common to all platforms
    common = [
        "paddleocr>=2.7.0",
        "PyQt6>=6.4.0",
        "Pillow>=9.0.0",
        "pymupdf>=1.23.0",
    ]

    if os_name == "Darwin":
        # macOS — pip resolves the correct ARM or x86 wheel automatically
        print("\nInstalling packages for macOS...")
        if arch == "arm64":
            print("  Apple Silicon (ARM) detected — CPU-only PaddlePaddle will be used.")
        run(
            [sys.executable, "-m", "pip", "install", "paddlepaddle>=2.5.0"] + common,
            "Installing PaddlePaddle + dependencies",
        )

    elif os_name == "Windows":
        print("\nInstalling packages for Windows...")
        if "ARM" in arch.upper():
            print(
                "  Windows ARM detected — PaddlePaddle has no native ARM wheel.\n"
                "  Installing x86 wheel; it will run via emulation (slower but functional)."
            )
        # Install PaddlePaddle CPU wheel first, then the rest
        run(
            [sys.executable, "-m", "pip", "install", "paddlepaddle>=2.5.0"],
            "Installing PaddlePaddle (CPU)",
        )
        run(
            [sys.executable, "-m", "pip", "install"] + common,
            "Installing remaining packages",
        )

    elif os_name == "Linux":
        print("\nInstalling packages for Linux...")
        run(
            [sys.executable, "-m", "pip", "install", "paddlepaddle>=2.5.0"] + common,
            "Installing all packages",
        )

    else:
        print(f"\nUnknown OS '{os_name}' — attempting generic install...")
        run(
            [sys.executable, "-m", "pip", "install", "paddlepaddle>=2.5.0"] + common,
            "Installing all packages",
        )


def verify_install():
    print("\nVerifying installation...")
    checks = [
        ("paddleocr", "PaddleOCR"),
        ("fitz",      "PyMuPDF"),
        ("PyQt6",     "PyQt6"),
        ("PIL",       "Pillow"),
    ]
    all_ok = True
    for module, name in checks:
        try:
            __import__(module)
            print(f"  ok  {name}")
        except ImportError:
            print(f"  FAIL  {name}")
            all_ok = False
    return all_ok


def main():
    print("=" * 52)
    print("  SearchPDF — Installer")
    print("=" * 52)

    check_python()

    os_name = platform.system()   # 'Darwin', 'Windows', 'Linux'
    arch    = platform.machine()  # 'arm64', 'x86_64', 'AMD64', 'ARM64'
    print(f"OS: {os_name}  |  Architecture: {arch}\n")

    upgrade_pip()
    install_packages(os_name, arch)

    ok = verify_install()

    print("\n" + "=" * 52)
    if ok:
        print("  Installation complete.")
        print("  Start the app with:  python main.py")
    else:
        print("  One or more packages failed.")
        print("  Try manually:  pip install paddleocr pymupdf PyQt6 Pillow")
    print("=" * 52)


if __name__ == "__main__":
    main()
